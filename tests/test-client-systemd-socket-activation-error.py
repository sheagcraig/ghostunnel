#!/usr/bin/env python3

"""
Spins up a client and tests systemd socket activation.
"""

from common import LOCALHOST, RootCert, STATUS_PORT, SocketPair, TcpClient, TlsServer, print_ok, run_ghostunnel, terminate
from distutils.spawn import find_executable
import sys

if __name__ == "__main__":
    ghostunnel = None

    try:
        # create certs
        root = RootCert('root')
        root.create_signed_cert('client')

        # start ghostunnel
        ghostunnel = run_ghostunnel([
                'client',
                '--listen=systemd:client',
                '--target={0}:{1}'.format(LOCALHOST, STATUS_PORT),
                '--keystore=client.p12',
                '--status=systemd:status',
                '--cacert=root.crt'])

        ghostunnel.wait(timeout=10)
        if ghostunnel.returncode == 0:
            raise Exception('Should fail on invalid socket')

        if not find_executable('systemd-socket-activate'):
            print_ok('skipping systemd socket activation test, no systemd-socket-activate binary found')
            sys.exit(0)

        # start ghostunnel
        ghostunnel = run_ghostunnel([
                'client',
                '--listen=systemd:client',
                '--target={0}:{1}'.format(LOCALHOST, STATUS_PORT),
                '--keystore=client.p12',
                '--status=systemd:status',
                '--cacert=root.crt'],
                prefix=[
                'systemd-socket-activate',
                '--listen={0}:13001'.format(LOCALHOST),
                '--listen={0}:{1}'.format(LOCALHOST, STATUS_PORT),
                # wrong fdname provided to test error checking
                '--fdname=server:status',
                '-E=GHOSTUNNEL_INTEGRATION_TEST',
                '-E=GHOSTUNNEL_INTEGRATION_ARGS',
                ])

        if ghostunnel.returncode == 0:
            raise Exception('Should fail on invalid socket')

        print_ok("OK")
    finally:
        terminate(ghostunnel)
