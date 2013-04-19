#!/usr/bin/python3

import apt
import apt_pkg
import os
import unittest

import unattended_upgrade

apt_pkg.config.set("APT::Architecture", "i386")


class LogInstallProgressMock(unattended_upgrade.LogInstallProgress):

    # klass data so that we can veriy in the test as the actual
    # object is destroyed
    DATA = []

    # overwrite to log the data
    def status_change(self, pkg, percent, status):
        print(pkg, percent)
        self.DATA.append([pkg, percent])


class TestMinimalPartitions(unittest.TestCase):

    def setUp(self):
        apt_pkg.config.set("Dir::State::status",
                           "./root.minimal-upgrade-steps/var/lib/dpkg/status")
        apt_pkg.config.set("Debug::NoLocking", "1")
        apt_pkg.config.set("Debug::pkgDPkgPM", "1")
        apt_pkg.config.clear("Dpkg::Post-Invoke")
        apt_pkg.config.clear("Dpkg::Pre-Install-Pkgs")
        self.cache = apt.Cache(rootdir="./root.minimal-upgrade-steps")

    def tearDown(self):
        if os.path.exists("./extended_states"):
            os.remove("./extended_states")

    def test_upgrade_in_minimal_steps(self):
        self.cache.upgrade(True)
        pkgs_to_upgrade = [pkg.name for pkg in self.cache.get_changes()]
        unattended_upgrade.PROGRESS_LOG = \
            "./aptroot/var/run/unatteded-upgrades.progress"
        unattended_upgrade.LogInstallProgress = LogInstallProgressMock
        unattended_upgrade.upgrade_in_minimal_steps(
            self.cache, pkgs_to_upgrade, "", [])
        # ensure we count upwarts
        last_percent = -1
        for (pkg, percent) in LogInstallProgressMock.DATA:
            self.assertTrue(last_percent < percent)
            last_percent = percent
        # cleanup class data
        LogInstallProgressMock.DATA = []

    def _get_all_upgradable(self):
        pkgs_to_upgrade = set()
        self.cache.upgrade(True)
        for pkg in self.cache.get_changes():
            pkgs_to_upgrade.add(pkg.name)
        self.cache.clear()
        return pkgs_to_upgrade

    def test_find_all_upgrade_partitions(self):
        # XXX write proper fixtures
        pkgs_to_upgrade = self._get_all_upgradable()
        partitions = unattended_upgrade._find_all_upgrade_partitions(
            self.cache, pkgs_to_upgrade, blacklist=[])
        seen = set()
        for part in partitions:
            seen = seen.union(set(part))
        self.assertEqual(seen, set(pkgs_to_upgrade))

    def test_upgrade_in_minimal_steps_speedup(self):
        # XXX write proper fixtures
        blacklist = []
        logfile_dpkg = ""
        pkgs_to_upgrade = self._get_all_upgradable()
        print(pkgs_to_upgrade)
        unattended_upgrade.check_changes_for_sanity = lambda *args: True
        unattended_upgrade.upgrade_in_minimal_steps(
            self.cache, pkgs_to_upgrade, blacklist, logfile_dpkg)


if __name__ == "__main__":
    #import logging
    #logging.basicConfig(level=logging.DEBUG)
    unittest.main()
