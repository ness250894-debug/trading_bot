from .base import BaseRepository
from datetime import datetime
import json
from app.core.resilience import retry

class BillingRepository(BaseRepository):
    # Subscription Methods
    def create_subscription(self, user_id, plan_id, status, expires_at):
        """Create or update a user subscription."""
        try:
            # Check if subscription exists
            existing = self.conn.execute(
                "SELECT 1 FROM subscriptions WHERE user_id = ?",
                [user_id]
            ).fetchone()
            
            if existing:
                query = """
                    UPDATE subscriptions 
                    SET plan_id = ?, status = ?, updated_at = ?, expires_at = ?
                    WHERE user_id = ?
                """
                self.conn.execute(query, [
                    plan_id,
                    status,
                    datetime.now(),
                    expires_at,
                    user_id
                ])
            else:
                query = """
                    INSERT INTO subscriptions (id, user_id, plan_id, status, starts_at, expires_at, updated_at)
                    VALUES (nextval('seq_subscription_id'), ?, ?, ?, ?, ?, ?)
                """
                self.conn.execute(query, [
                    user_id,
                    plan_id,
                    status,
                    datetime.now(),
                    expires_at,
                    datetime.now()
                ])
            return True
        except Exception as e:
            self.logger.error(f"Error creating subscription: {e}")
            return False

    def get_subscription(self, user_id):
        """Get user subscription."""
        try:
            result = self.conn.execute(
                "SELECT * FROM subscriptions WHERE user_id = ?",
                [user_id]
            ).fetchone()
            
            if not result:
                return None
                
            return {
                'id': result[0],
                'user_id': result[1],
                'plan_id': result[2],
                'status': result[3],
                'starts_at': result[4],
                'expires_at': result[5],
                'updated_at': result[7] if len(result) > 7 else None
            }
        except Exception as e:
            self.logger.error(f"Error fetching subscription: {e}")
            return None
    
    def is_subscription_active(self, user_id, is_admin=False):
        """
        Check if user has an active, non-expired subscription.
        Args:
            user_id: The user ID
            is_admin: If true, bypass checks (callers responsibility to pass this)
        """
        try:
            if is_admin:
                return True

            subscription = self.get_subscription(user_id)
            if not subscription:
                return False
            
            # Check status
            if subscription.get('status') != 'active':
                return False
            
            # Check expiration date
            expires_at = subscription.get('expires_at')
            if not expires_at:
                return False
                
            # Handle string dates from database if any
            if isinstance(expires_at, str):
                try:
                    expires_at = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
                except (ValueError, TypeError) as e:
                    self.logger.error(f"Failed to parse expiration date '{expires_at}': {e}")
                    return False
            
            # Check if not expired
            return datetime.now() < expires_at
            
        except Exception as e:
            self.logger.error(f"Error checking subscription status: {e}")
            # Fail-safe: allow trading if check fails to avoid blocking legitimate users?
            # Or strict? Following original logic: return True on error (fail-open)
            return True

    def create_payment(self, user_id, charge_code, amount, currency, plan_id):
        """Log a new payment attempt."""
        try:
            query = """
                INSERT INTO payments 
                (id, user_id, charge_code, amount, currency, status, plan_id, created_at)
                VALUES (nextval('seq_payment_id'), ?, ?, ?, ?, 'created', ?, ?)
            """
            self.conn.execute(query, [
                user_id,
                charge_code,
                amount,
                currency,
                plan_id,
                datetime.now()
            ])
            return True
        except Exception as e:
            self.logger.error(f"Error creating payment: {e}")
            return False


    def get_payment_by_charge_code(self, charge_code):
        """Get payment details by charge code."""
        try:
            result = self.conn.execute(
                "SELECT * FROM payments WHERE charge_code = ?",
                [charge_code]
            ).fetchone()
            
            if not result:
                return None
            
            return {
                'id': result[0],
                'user_id': result[1],
                'charge_code': result[2],
                'amount': result[3],
                'currency': result[4],
                'status': result[5],
                'plan_id': result[6],
                'created_at': result[7],
                'confirmed_at': result[8] if len(result) > 8 else None
            }
        except Exception as e:
            self.logger.error(f"Error fetching payment: {e}")
            return None

    def update_payment_status(self, charge_code, status):
        """Update payment status."""
        try:
            self.conn.execute(
                "UPDATE payments SET status = ?, confirmed_at = ? WHERE charge_code = ?",
                [status, datetime.now() if status == 'confirmed' else None, charge_code]
            )
            self.logger.info(f"Payment {charge_code} updated to {status}")
            return True
        except Exception as e:
            self.logger.error(f"Error updating payment: {e}")
            return False

    # Plan Management Methods
    def get_plans(self):
        """Get all active plans."""
        try:
            results = self.conn.execute("SELECT * FROM plans WHERE is_active = TRUE ORDER BY price ASC").fetchall()
            plans = []
            for r in results:
                plans.append({
                    'id': r[0],
                    'name': r[1],
                    'price': r[2],
                    'currency': r[3],
                    'duration_days': r[4],
                    'features': json.loads(r[5]) if r[5] else [],
                    'is_active': bool(r[6]),
                    'created_at': str(r[7]),
                    'updated_at': str(r[8])
                })
            return plans
        except Exception as e:
            self.logger.error(f"Error fetching plans: {e}")
            return []

    def get_all_plans(self):
        """Get all plans (active and inactive)."""
        try:
            results = self.conn.execute("SELECT * FROM plans ORDER BY price ASC").fetchall()
            plans = []
            for r in results:
                plans.append({
                    'id': r[0],
                    'name': r[1],
                    'price': r[2],
                    'currency': r[3],
                    'duration_days': r[4],
                    'features': json.loads(r[5]) if r[5] else [],
                    'is_active': bool(r[6]),
                    'created_at': str(r[7]),
                    'updated_at': str(r[8])
                })
            return plans
        except Exception as e:
            self.logger.error(f"Error fetching all plans: {e}")
            return []

    def get_plan(self, plan_id):
        """Get a specific plan."""
        try:
            result = self.conn.execute("SELECT * FROM plans WHERE id = ?", [plan_id]).fetchone()
            if not result:
                return None
            return {
                'id': result[0],
                'name': result[1],
                'price': result[2],
                'currency': result[3],
                'duration_days': result[4],
                'features': json.loads(result[5]) if result[5] else [],
                'is_active': bool(result[6]),
                'created_at': str(result[7]),
                'updated_at': str(result[8])
            }
        except Exception as e:
            self.logger.error(f"Error fetching plan: {e}")
            return None

    def create_plan(self, plan_data):
        """Create a new plan."""
        try:
            query = """
                INSERT INTO plans (id, name, price, currency, duration_days, features, is_active, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            self.conn.execute(query, [
                plan_data['id'],
                plan_data['name'],
                plan_data['price'],
                plan_data['currency'],
                plan_data['duration_days'],
                json.dumps(plan_data.get('features', [])),
                plan_data.get('is_active', True),
                datetime.now(),
                datetime.now()
            ])
            self.logger.info(f"Plan created: {plan_data['id']}")
            return True
        except Exception as e:
            self.logger.error(f"Error creating plan: {e}")
            return False

    def update_plan(self, plan_id, plan_data):
        """Update an existing plan."""
        try:
            # Build update query dynamically based on provided fields
            fields = []
            values = []
            
            if 'name' in plan_data:
                fields.append("name = ?")
                values.append(plan_data['name'])
            if 'price' in plan_data:
                fields.append("price = ?")
                values.append(plan_data['price'])
            if 'currency' in plan_data:
                fields.append("currency = ?")
                values.append(plan_data['currency'])
            if 'duration_days' in plan_data:
                fields.append("duration_days = ?")
                values.append(plan_data['duration_days'])
            if 'features' in plan_data:
                fields.append("features = ?")
                values.append(json.dumps(plan_data['features']))
            if 'is_active' in plan_data:
                fields.append("is_active = ?")
                values.append(plan_data['is_active'])
                
            fields.append("updated_at = ?")
            values.append(datetime.now())
            
            values.append(plan_id)
            
            query = f"UPDATE plans SET {', '.join(fields)} WHERE id = ?"
            self.conn.execute(query, values)
            self.logger.info(f"Plan updated: {plan_id}")
            return True
        except Exception as e:
            self.logger.error(f"Error updating plan: {e}")
            return False

    def delete_plan(self, plan_id):
        """Delete a plan permanently."""
        try:
            # Check if plan is in use
            usage = self.conn.execute("SELECT count(*) FROM subscriptions WHERE plan_id = ?", [plan_id]).fetchone()
            if usage and usage[0] > 0:
                self.logger.warning(f"Cannot delete plan {plan_id}: In use by {usage[0]} subscriptions.")
                return False # Or raise error to inform user? User said "should delete".
                # If I return False, the API returns 500 "Failed to delete".
                # Standard SQL behavior is to fail if FK exists (if protected).
                # But DuckDB might not enforce FKs rigorously unless configured.
                # Safer to block here if used.
            
            # Hard delete
            self.conn.execute("DELETE FROM plans WHERE id = ?", [plan_id])
            return True
        except Exception as e:
            self.logger.error(f"Error deleting plan: {e}")
            return False

    def update_user_subscription(self, user_id, plan_id, status):
        """Admin update of user subscription."""
        try:
            from datetime import timedelta
            
            # Set expiration based on plan (default 30 days if not specified)
            duration = 365 if 'yearly' in plan_id else 30
            expires_at = datetime.now() + timedelta(days=duration)
            
            return self.create_subscription(user_id, plan_id, status, expires_at)
        except Exception as e:
            self.logger.error(f"Error updating user subscription: {e}")
            return False

    def get_user_features(self, user_id, is_admin=False):
        """
        Get list of features enabled for the user.
        Returns a list of feature strings (e.g. ['live_trading', 'max_bots_10']).
        """
        if is_admin:
            # Admins have all features implicitly, but explicitly returning a set of super-features 
            # might be safer. For now, we return a special flag or just all known features?
            # Creating a super-set of keys for admins:
            return [
                "live_trading", "max_bots_unlimited", "visual_builder", "backtesting", 
                "optimization_ultimate", "sentiment_advanced", "quick_scalp", 
                "priority_support", "unlimited_exchanges"
            ]

        try:
            # 1. Check if subscription is active
            if not self.is_subscription_active(user_id):
                return [] # Free plan has no "features" currently, or add defaults here if needed.

            # 2. Get Plan ID from subscription
            sub = self.get_subscription(user_id)
            if not sub:
                return []
            
            plan_id = sub['plan_id']
            
            # 3. Get Features from Plan
            # Join would be more efficient but we have helpers.
            plan = self.get_plan(plan_id)
            if not plan:
                return []
            
            return plan.get('features', [])
            
        except Exception as e:
            self.logger.error(f"Error getting user features: {e}")
            return []
