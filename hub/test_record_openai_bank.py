"""Budget guard tests; no credential reads or provider calls."""
from decimal import Decimal
import unittest
import record_openai_bank as r

class BudgetTests(unittest.TestCase):
    def test_actual_mixed_usage(self):
        self.assertEqual(r.cost({'input_tokens':1000,'output_tokens':210,'input_token_details':{'audio_tokens':0},'output_token_details':{'audio_tokens':200}}),Decimal('0.004624'))
    def test_unknown_usage_keeps_reservation(self):
        self.assertEqual(r.cost({}),r.RESERVE)
    def test_reservation_exceeds_capped_request(self):
        # Every input byte treated as a token; all output tokens at higher rate.
        worst=(Decimal(6000)*Decimal('.60')+Decimal(1200)*20)/1000000
        self.assertLess(worst,r.RESERVE)
    def test_no_audio_details_charges_high_output_rate(self):
        self.assertEqual(r.cost({'input_tokens':1000,'output_tokens':200}),Decimal('.0046'))

if __name__=='__main__':unittest.main()
