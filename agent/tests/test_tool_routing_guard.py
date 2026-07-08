import unittest

from src.tools.routing_guard import evaluate_tool_asset_compatibility


class ToolRoutingGuardTest(unittest.TestCase):
    def _route(self, tool_name, asset_type, *, market="CN", symbol="600519.SH"):
        return evaluate_tool_asset_compatibility(
            tool_name=tool_name,
            symbol=symbol,
            market=market,
            asset_type=asset_type,
        )

    def test_market_data_allows_stock(self):
        self.assertEqual(self._route("get_market_data", "stock")["decision"], "allow")

    def test_market_data_allows_index(self):
        self.assertEqual(self._route("get_market_data", "index", symbol="000001.SH")["decision"], "allow")

    def test_market_data_allows_etf(self):
        self.assertEqual(self._route("get_market_data", "etf", symbol="510300.SH")["decision"], "allow")

    def test_sector_info_allows_stock(self):
        self.assertEqual(self._route("get_sector_info", "stock")["decision"], "allow")

    def test_sector_info_blocks_index(self):
        self.assertEqual(self._route("get_sector_info", "index", symbol="000001.SH")["decision"], "block")

    def test_sector_info_blocks_etf(self):
        self.assertEqual(self._route("get_sector_info", "etf", symbol="510300.SH")["decision"], "block")

    def test_financial_statements_allow_stock(self):
        self.assertEqual(self._route("get_financial_statements", "stock")["decision"], "allow")

    def test_financial_statements_block_index(self):
        self.assertEqual(self._route("get_financial_statements", "index", symbol="000001.SH")["decision"], "block")

    def test_financial_statements_block_etf(self):
        self.assertEqual(self._route("get_financial_statements", "etf", symbol="510300.SH")["decision"], "block")

    def test_shareholder_count_allows_stock(self):
        self.assertEqual(self._route("get_shareholder_count", "stock")["decision"], "allow")

    def test_shareholder_count_blocks_index(self):
        self.assertEqual(self._route("get_shareholder_count", "index", symbol="000001.SH")["decision"], "block")

    def test_margin_trading_allows_a_share_stock(self):
        self.assertEqual(self._route("get_margin_trading", "stock", market="CN")["decision"], "allow")

    def test_margin_trading_warns_a_share_etf(self):
        self.assertEqual(self._route("get_margin_trading", "etf", market="CN", symbol="510300.SH")["decision"], "warn")

    def test_margin_trading_blocks_index(self):
        self.assertEqual(self._route("get_margin_trading", "index", symbol="000001.SH")["decision"], "block")

    def test_block_trades_allows_stock(self):
        self.assertEqual(self._route("get_block_trades", "stock")["decision"], "allow")

    def test_block_trades_blocks_index(self):
        self.assertEqual(self._route("get_block_trades", "index", symbol="000001.SH")["decision"], "block")

    def test_block_trades_warns_etf(self):
        self.assertEqual(self._route("get_block_trades", "etf", symbol="510300.SH")["decision"], "warn")

    def test_stock_news_allows_stock(self):
        self.assertEqual(self._route("get_stock_news", "stock")["decision"], "allow")

    def test_stock_news_warns_index(self):
        self.assertEqual(self._route("get_stock_news", "index", symbol="000001.SH")["decision"], "warn")

    def test_stock_news_warns_etf(self):
        self.assertEqual(self._route("get_stock_news", "etf", symbol="QQQ.US", market="US")["decision"], "warn")

    def test_web_search_allows_index(self):
        result = self._route("web_search", "index", symbol="000001.SH")
        self.assertEqual(result["decision"], "allow")
        self.assertEqual(result["metadata"]["source_type"], "web_unstructured")

    def test_read_url_allows_etf(self):
        result = self._route("read_url", "etf", symbol="QQQ.US", market="US")
        self.assertEqual(result["decision"], "allow")
        self.assertEqual(result["metadata"]["source_type"], "web_unstructured")

    def test_search_symbol_allows_unknown(self):
        result = self._route("search_symbol", "unknown", symbol=None, market=None)
        self.assertEqual(result["decision"], "allow")
        self.assertEqual(result["metadata"]["source_type"], "discovery")

    def test_stock_specific_tool_with_unknown_asks_for_confirmation(self):
        result = self._route("get_sector_info", None, symbol="000001")
        self.assertEqual(result["decision"], "ask_for_confirmation")

    def test_unsupported_tool_allows_with_reason(self):
        result = self._route("some_future_tool", "index", symbol="000001.SH")
        self.assertEqual(result["decision"], "allow")
        self.assertEqual(result["reason"], "unsupported_tool_for_mvp")
        self.assertFalse(result["metadata"]["guarded"])

    def test_asset_type_is_case_insensitive(self):
        self.assertEqual(self._route("get_market_data", "ETF", symbol="QQQ.US", market="US")["decision"], "allow")

    def test_market_is_case_insensitive_for_a_share_margin(self):
        self.assertEqual(self._route("get_margin_trading", "stock", market="a-SHARE")["decision"], "allow")


if __name__ == "__main__":
    unittest.main()
