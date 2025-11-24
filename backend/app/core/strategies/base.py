from abc import ABC, abstractmethod

class Strategy(ABC):
    @abstractmethod
    def generate_signal(self, dataframe):
        """
        Analyzes the dataframe and returns a signal.
        Returns:
            dict: {'signal': 'BUY'/'SELL'/'HOLD', 'score': int, 'details': dict}
        """
        pass

    def calculate_indicators(self, dataframe):
        """
        Calculates indicators for the entire dataframe.
        Returns:
            dataframe: Dataframe with new indicator columns.
        """
        return dataframe

    def check_signal(self, row):
        """
        Checks signal for a single row (Series).
        Returns:
            dict: {'signal': 'BUY'/'SELL'/'HOLD', 'score': int, 'details': dict}
        """
        return {'signal': 'HOLD', 'score': 0, 'details': {}}
