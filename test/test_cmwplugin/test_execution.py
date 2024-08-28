##############################################################################
# COPYRIGHT Ericsson AB 2014
#
# The copyright to the computer program(s) herein is the property of
# Ericsson AB. The programs may be used and/or copied only with written
# permission from Ericsson AB. or in accordance with the terms and
# conditions stipulated in the agreement/contract under which the
# program(s) have been supplied.
##############################################################################


#from cmwplugin.execution import execute_ms, execute

import unittest
import mock


class ExecutionTestCase(unittest.TestCase):
    def setUp(self):
        self.patcher = mock.patch('cmwplugin.execution.subprocess.Popen')
        self.mock_popen = self.patcher.start()
        self.mock_popen.return_value.communicate.return_value = ('STDOUT',
                                                                 'STDERR')
        self.mock_popen.return_value.wait.return_value = 0

    def tearDown(self):
        self.patcher.stop()

    def est_execute_ms(self):
        command = 'do_me_now'
        expected = (0, 'STDOUT', 'STDERR')
        result = execute_ms(command)
        self.assertEqual(expected, result)
        self.mock_popen.assert_called_once_with([command],
                                                shell=True,
                                                stdout=-1)

    def est_execute_escapes_command_string(self):
        hosts = ['host1', 'host2']
        command = mock.MagicMock()
        command.__str__.return_value = 'do_me_now'
        command.replace.return_value = command
        execute(hosts, command)
        command.replace.assert_any_call("\"", "\\\"")
        command.replace.assert_any_call(";", "\;")

    def est_execute_returns_list_of_tuples(self):
        command = 'do_me_now'
        expected = (0, 'STDOUT', 'STDERR')
        hosts = ['host1', 'host2']
        result = execute(hosts, command)
        self.assertEqual(len(hosts), len(result))
        self.assertEqual(expected, result[0])
        self.assertEqual(expected, result[1])

    def est_execute_returns_one_tuple_for_single_host(self):
        command = 'do_me_now'
        expected = (0, 'STDOUT', 'STDERR')
        hosts = ['host1']
        result = execute(hosts, command)
        # result is a stdout, stderr single tuple
        self.assertEqual(expected[0], result[0])
        self.assertEqual(expected[1], result[1])

    def est_execute_sends_command_to_each_host(self):
        hosts = ['host1', 'host2']
        command = 'do_me_now'
        execute(hosts, command)
        # correct number of Popen created
        self.assertEqual(2,
                         self.mock_popen.call_count)
        self.assertEqual(len(hosts),
                         self.mock_popen.return_value.communicate.call_count)

    def est_execute_uses_root_user_with_default_password(self):
        hosts = ['host1']
        command = 'do_me_now'
        execute(hosts, command)
        args, kwargs = self.mock_popen.call_args_list[0]
        self.assertTrue('root@host1' in args[0][0])
        self.assertTrue('litpc0b6lEr' in args[0][0])

    def est_execute_updates_password_when_expired(self):
        hosts = ['host1']
        command = 'do_me_now'
        expected = ('Your password has expired', 'STDERR')
        self.mock_popen.return_value.communicate.return_value = expected
        execute(hosts, command)
        #print self.mock_popen.call_count
        #print self.mock_popen.call_args_list
        # TODO test if calls to switch password appear in the call_arg_list
