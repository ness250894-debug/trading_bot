import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from app.core.services.bot_service import BotService

@pytest.fixture
def mock_deps():
    with patch('app.core.services.bot_service.DuckDBHandler') as mock_db_cls, \
         patch('app.core.services.bot_service.bot_manager') as mock_bm, \
         patch('app.core.services.bot_service.socket_manager') as mock_sm, \
         patch('app.core.services.bot_service.EncryptionHelper') as mock_enc_cls:
        
        mock_db = mock_db_cls.return_value
        mock_enc = mock_enc_cls.return_value
        
        yield {
            'db': mock_db,
            'bm': mock_bm,
            'sm': mock_sm,
            'enc': mock_enc
        }

@pytest.fixture
def service(mock_deps):
    return BotService()

@pytest.mark.asyncio
async def test_start_bot_success(service, mock_deps):
    user_id = 1
    config_id = 101
    
    # Setup mocks
    mock_deps['db'].get_bot_config.return_value = {
        'symbol': 'BTC/USDT',
        'timeframe': '5m',
        'amount_usdt': 100,
        'strategy': 'mean_reversion',
        'dry_run': True,
        'take_profit_pct': 0.01,
        'stop_loss_pct': 0.01
    }
    mock_deps['db'].get_user_by_id.return_value = {'is_admin': False}
    # Mock subscription to be active Pro
    mock_deps['db'].get_subscription.return_value = None # Defaults to Free/check logic
    # Actually, let's mock free plan but dry run = True (allowed)
    
    mock_deps['bm'].start_bot.return_value = True
    
    # Execute
    result = service.start_bot(user_id, config_id=config_id)
    
    # Verify
    assert result is True
    mock_deps['bm'].start_bot.assert_called_once()
    
    # Broadcast should have been called (it's async task)
    # Since start_bot uses asyncio.create_task, we might not see it awaited immediately 
    # unless we use a better async test pattern or mock create_task.
    # But checking if logic reached there is enough.

def test_enforce_subscription_free_plan_violation(service, mock_deps):
    user_id = 1
    config = {'DRY_RUN': False, 'STRATEGY': 'mean_reversion'} # Live trading
    
    # Mock Free Plan
    mock_deps['db'].get_subscription.return_value = {'status': 'active', 'plan_id': 'free_monthly', 'expires_at': None}
    
    # Should raise 403 because Live Trading not allowed on Free
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc:
        service._enforce_subscription(user_id, config, is_admin=False)
    assert exc.value.status_code == 403
    assert "Live trading requires" in exc.value.detail

@pytest.mark.asyncio
async def test_stop_bot_success(service, mock_deps):
    user_id = 1
    config_id = 101
    
    mock_deps['bm'].stop_bot.return_value = True
    
    result = service.stop_bot(user_id, config_id=config_id)
    
    assert result is True
    mock_deps['bm'].stop_bot.assert_called_once()
