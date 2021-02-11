import unittest
from unittest.mock import MagicMock, patch

from lemon_pi.pit.datasource.datasource_handler import DataSourceHandler
from lemon_pi.pit.leaderboard import RaceOrder


class DatasourceHandlerTestCase(unittest.TestCase):

    @patch("lemon_pi.pit.event_defs.RaceStatusEvent.emit")
    def test_flags(self, emit:MagicMock):
        ro = RaceOrder()
        dsh = DataSourceHandler(ro, "100")
        dsh.handle_message('$F,9999,"00:00:00","11:15:05","02:15:35","Red   "')
        emit.assert_called_with(flag="Red")
        dsh.handle_message('$F,9999,"00:00:00","11:15:05","02:15:35","Green "')
        emit.assert_called_with(flag="Green")
        dsh.handle_message('$F,9999,"00:00:00","11:15:08","02:15:38","Yellow"')
        emit.assert_called_with(flag="Yellow")
        dsh.handle_message('$F,9999,"00:00:00","14:17:35","00:36:46","Finish"')
        emit.assert_called_with(flag="Finish")
        dsh.handle_message('$F,0,"00:00:00","14:20:58","00:00:00","      "')
        emit.assert_called_with(flag="")


    def test_two_cars(self):
        ro = RaceOrder()
        dsh = DataSourceHandler(ro, "100")
        for line in test_file.splitlines():
            dsh.handle_message(line)
        self.assertEqual("181", ro.first.car_number)

    def test_large_file(self):
        ro = RaceOrder()
        dsh = DataSourceHandler(ro, "100")
        with open('resources/test/test-file.dat') as f:
            for line in f.readlines():
                dsh.handle_message(line)
        self.assertEqual("160", ro.first.car_number)


test_file = """
$RMDTL,""
$RMCA,1610910893000
$A,"181","181",8860657,"","The Perplexus","Lexus",1
$A,"183","183",1299027,"Missfits","","Mazda 323",1
$B,27,"Sun 7.5Hr"
$C,1,"LDRL A"
$COMP,"181","181",1,"","The Perplexus","Lexus"
$COMP,"183","183",1,"Missfits","","Mazda 323"
$G,1,"181",2,"02:00:40.326"
$G,2,"183",2,"02:00:24.529"
$H,1,"181",1,"00:01:45.418"
$H,2,"183",1,"00:01:49.342"
$J,"181","00:02:08.239","01:58:38.485"
$J,"183","00:02:21.597","01:59:55.687"
$RMS,"race"
$RMLT,181,1610909938000
$RMLT,183,1610909791000
$F,9999,"00:00:00","11:15:08","02:15:38","Yellow"
$F,9999,"00:00:00","11:15:09","02:15:39","Green "
$RMHL,"181","2","1","00:17:00.746","Green ","02:15:39.231"
$RMHL,"183","2","2","00:17:02.091","Green ","02:15:41.712"
"""

if __name__ == '__main__':
    unittest.main()
