"""
Condition evaluation engine for JSON-based strategies.
Evaluates trading conditions and logic operators.
"""
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Union


class ConditionEvaluator:
    """Evaluates trading conditions from JSON configuration."""
    
    @staticmethod
    def evaluate_condition(condition: Dict[str, Any], df: pd.DataFrame, current_idx: int) -> bool:
        """
        Evaluate a single condition.
        
        Args:
            condition: Condition configuration
            df: OHLCV dataframe with indicators
            current_idx: Current row index
            
        Returns:
            Boolean result of condition
        """
        operator = condition.get('operator', '==')
        left = condition.get('left')
        right = condition.get('right')
        
        # Get left value
        left_val = ConditionEvaluator._get_value(left, df, current_idx)
        
        # Get right value
        right_val = ConditionEvaluator._get_value(right, df, current_idx)
        
        # Handle None values
        if left_val is None or right_val is None:
            return False
        
        # Check for NaN
        if pd.isna(left_val) or pd.isna(right_val):
            return False
        
        # Evaluate based on operator
        if operator == '>':
            return float(left_val) > float(right_val)
        elif operator == '<':
            return float(left_val) < float(right_val)
        elif operator == '>=':
            return float(left_val) >= float(right_val)
        elif operator == '<=':
            return float(left_val) <= float(right_val)
        elif operator == '==':
            return float(left_val) == float(right_val)
        elif operator == '!=':
            return float(left_val) != float(right_val)
        elif operator == 'crosses_above':
            return ConditionEvaluator._check_cross_above(left, right, df, current_idx)
        elif operator == 'crosses_below':
            return ConditionEvaluator._check_cross_below(left, right, df, current_idx)
        elif operator == 'between':
            # right should be [min, max]
            if isinstance(right, list) and len(right) == 2:
                return float(right[0]) <= float(left_val) <= float(right[1])
            return False
        elif operator == 'outside_range':
            # right should be [min, max]
            if isinstance(right, list) and len(right) == 2:
                return float(left_val) < float(right[0]) or float(left_val) > float(right[1])
            return False
        else:
            raise ValueError(f"Unsupported operator: {operator}")
    
    @staticmethod
    def evaluate_logic(logic: Dict[str, Any], df: pd.DataFrame, current_idx: int) -> bool:
        """
        Evaluate logic operators (AND, OR, NOT).
        
        Args:
            logic: Logic configuration with operator and conditions
            df: OHLCV dataframe with indicators
            current_idx: Current row index
            
        Returns:
            Boolean result of logic evaluation
        """
        operator = logic.get('operator', 'AND')
        rules = logic.get('rules', [])
        
        if not rules:
            return False
        
        results = []
        for rule in rules:
            # Check if this is a nested logic block
            if 'operator' in rule and 'rules' in rule:
                results.append(ConditionEvaluator.evaluate_logic(rule, df, current_idx))
            else:
                results.append(ConditionEvaluator.evaluate_condition(rule, df, current_idx))
        
        if operator == 'AND':
            return all(results)
        elif operator == 'OR':
            return any(results)
        elif operator == 'NOT':
            # NOT should have only one rule
            return not results[0] if results else False
        else:
            raise ValueError(f"Unsupported logic operator: {operator}")
    
    @staticmethod
    def _get_value(ref: Union[str, int, float], df: pd.DataFrame, current_idx: int) -> Union[float, None]:
        """
        Get value from reference (column name or literal).
        
        Args:
            ref: Reference to column or literal value
            df: OHLCV dataframe
            current_idx: Current row index
            
        Returns:
            Value
        """
        # If it's a number, return it
        if isinstance(ref, (int, float)):
            return float(ref)
        
        # If it's a string, try to get from dataframe
        if isinstance(ref, str):
            if ref in df.columns:
                try:
                    return float(df.iloc[current_idx][ref])
                except (IndexError, KeyError):
                    return None
            else:
                # Try to parse as number
                try:
                    return float(ref)
                except ValueError:
                    return None
        
        return None
    
    @staticmethod
    def _check_cross_above(left: str, right: str, df: pd.DataFrame, current_idx: int) -> bool:
        """
        Check if left crosses above right.
        
        Args:
            left: Left indicator/column name
            right: Right indicator/column name
            df: OHLCV dataframe
            current_idx: Current row index
            
        Returns:
            True if cross above detected
        """
        if current_idx < 1:
            return False
        
        # Get current and previous values
        curr_left = ConditionEvaluator._get_value(left, df, current_idx)
        curr_right = ConditionEvaluator._get_value(right, df, current_idx)
        prev_left = ConditionEvaluator._get_value(left, df, current_idx - 1)
        prev_right = ConditionEvaluator._get_value(right, df, current_idx - 1)
        
        if any(v is None or pd.isna(v) for v in [curr_left, curr_right, prev_left, prev_right]):
            return False
        
        # Cross above: was below, now above
        return prev_left <= prev_right and curr_left > curr_right
    
    @staticmethod
    def _check_cross_below(left: str, right: str, df: pd.DataFrame, current_idx: int) -> bool:
        """
        Check if left crosses below right.
        
        Args:
            left: Left indicator/column name
            right: Right indicator/column name
            df: OHLCV dataframe
            current_idx: Current row index
            
        Returns:
            True if cross below detected
        """
        if current_idx < 1:
            return False
        
        # Get current and previous values
        curr_left = ConditionEvaluator._get_value(left, df, current_idx)
        curr_right = ConditionEvaluator._get_value(right, df, current_idx)
        prev_left = ConditionEvaluator._get_value(left, df, current_idx - 1)
        prev_right = ConditionEvaluator._get_value(right, df, current_idx - 1)
        
        if any(v is None or pd.isna(v) for v in [curr_left, curr_right, prev_left, prev_right]):
            return False
        
        # Cross below: was above, now below
        return prev_left >= prev_right and curr_left < curr_right
    
    @staticmethod
    def get_available_operators() -> Dict[str, Dict[str, Any]]:
        """
        Get metadata about all available operators.
        
        Returns:
            Dictionary of operator metadata
        """
        return {
            'comparison': {
                '>': {'name': 'Greater Than', 'symbol': '>', 'requires_two_values': True},
                '<': {'name': 'Less Than', 'symbol': '<', 'requires_two_values': True},
                '>=': {'name': 'Greater Than or Equal', 'symbol': '≥', 'requires_two_values': True},
                '<=': {'name': 'Less Than or Equal', 'symbol': '≤', 'requires_two_values': True},
                '==': {'name': 'Equal To', 'symbol': '=', 'requires_two_values': True},
                '!=': {'name': 'Not Equal To', 'symbol': '≠', 'requires_two_values': True},
            },
            'crosses': {
                'crosses_above': {'name': 'Crosses Above', 'symbol': '⤴', 'requires_two_values': True},
                'crosses_below': {'name': 'Crosses Below', 'symbol': '⤵', 'requires_two_values': True},
            },
            'range': {
                'between': {'name': 'Between', 'symbol': '⊆', 'requires_range': True},
                'outside_range': {'name': 'Outside Range', 'symbol': '⊄', 'requires_range': True},
            },
            'logic': {
                'AND': {'name': 'All Conditions (AND)', 'symbol': '∧'},
                'OR': {'name': 'Any Condition (OR)', 'symbol': '∨'},
                'NOT': {'name': 'Not (NOT)', 'symbol': '¬'},
            }
        }
