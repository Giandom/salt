# -tests/integration/daemons/test_masterapi.py:71*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

import os
import shutil
import stat

import salt.utils.files
import salt.utils.stringutils
from tests.support.case import ShellCase
from tests.support.helpers import slowTest
from tests.support.runtests import RUNTIME_VARS

# Import 3rd-party libs


class AutosignGrainsTest(ShellCase):
    """
    Test autosigning minions based on grain values.
    """

    def setUp(self):
        # all read, only owner write
        self.autosign_file_permissions = (
            stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH | stat.S_IWUSR
        )
        if RUNTIME_VARS.PYTEST_SESSION:
            self.autosign_file_path = os.path.join(RUNTIME_VARS.TMP, "autosign_file")
        else:
            self.autosign_file_path = os.path.join(
                RUNTIME_VARS.TMP, "rootdir", "autosign_file"
            )
        shutil.copyfile(
            os.path.join(RUNTIME_VARS.FILES, "autosign_grains", "autosign_file"),
            self.autosign_file_path,
        )
        os.chmod(self.autosign_file_path, self.autosign_file_permissions)

        self.run_key("-d minion -y")
        self.run_call(
            "test.ping -l quiet"
        )  # get minion to try to authenticate itself again

        if "minion" in self.run_key("-l acc"):
            self.tearDown()
            self.skipTest("Could not deauthorize minion")
        if "minion" not in self.run_key("-l un"):
            self.tearDown()
            self.skipTest("minion did not try to reauthenticate itself")

        self.autosign_grains_dir = os.path.join(self.master_opts["autosign_grains_dir"])
        if not os.path.isdir(self.autosign_grains_dir):
            os.makedirs(self.autosign_grains_dir)

    def tearDown(self):
        shutil.copyfile(
            os.path.join(RUNTIME_VARS.FILES, "autosign_file"), self.autosign_file_path
        )
        os.chmod(self.autosign_file_path, self.autosign_file_permissions)

        self.run_call("test.ping -l quiet")  # get minion to authenticate itself again

        try:
            if os.path.isdir(self.autosign_grains_dir):
                shutil.rmtree(self.autosign_grains_dir)
        except AttributeError:
            pass

    @slowTest
    def test_autosign_grains_accept(self):
        grain_file_path = os.path.join(self.autosign_grains_dir, "test_grain")
        with salt.utils.files.fopen(grain_file_path, "w") as f:
            f.write(salt.utils.stringutils.to_str("#invalid_value\ncheese"))
        os.chmod(grain_file_path, self.autosign_file_permissions)

        self.run_call(
            "test.ping -l quiet"
        )  # get minion to try to authenticate itself again
        self.assertIn("minion", self.run_key("-l acc"))

    @slowTest
    def test_autosign_grains_fail(self):
        grain_file_path = os.path.join(self.autosign_grains_dir, "test_grain")
        with salt.utils.files.fopen(grain_file_path, "w") as f:
            f.write(salt.utils.stringutils.to_str("#cheese\ninvalid_value"))
        os.chmod(grain_file_path, self.autosign_file_permissions)

        self.run_call(
            "test.ping -l quiet"
        )  # get minion to try to authenticate itself again
        self.assertNotIn("minion", self.run_key("-l acc"))
        self.assertIn("minion", self.run_key("-l un"))
