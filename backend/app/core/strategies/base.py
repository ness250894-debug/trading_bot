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

    def check_signal(self, current_row, previous_row=None):
        """
        Checks signal for a single row (Series).
        Args:
            current_row (pd.Series): The current row of data.
            previous_row (pd.Series, optional): The previous row of data. Defaults to None.
        Returns:
            dict: {'signal': 'BUY'/'SELL'/'HOLD', 'score': int, 'details': dict}
        """
        return {'signal': 'HOLD', 'score': 0, 'details': {}}

    def populate_indicators(self, dataframe):
        """
        Alias for calculate_indicators (Freqtrade compatibility).
        """
        return self.calculate_indicators(dataframe)

    def populate_buy_trend(self, dataframe):
        """
        Vectorized Buy Signal Generation.
        Should populate a 'buy' column with 1 (Buy) or 0 (No Buy).
        """
        dataframe['buy'] = 0
        return dataframe

    def populate_sell_trend(self, dataframe):
        """
        Vectorized Sell Signal Generation.
        Should populate a 'sell' column with 1 (Sell) or 0 (No Sell).
        """
        dataframe['sell'] = 0
        return dataframe
