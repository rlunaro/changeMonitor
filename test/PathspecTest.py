'''
Copyright 2023 superman_ha_muerto@yahoo.com

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

@author: rluna
'''
import unittest

import pathspec


class PathspecTest(unittest.TestCase):


    def setUp(self):
        pass


    def tearDown(self):
        pass


    def testBasic(self):
        spec_text = """

# This is a comment because the line begins with a hash: "#"

# Include several project directories (and all descendants) relative to
# the current directory. To reference a directory you must end with a
# slash: "/"
/project-a/
/project-b/
/project-c/

# Patterns can be negated by prefixing with exclamation mark: "!"

# Ignore temporary files beginning or ending with "~" and ending with
# ".swp".
!~*
!*~
!*.swp

# These are python projects so ignore compiled python files from
# testing.
!*.pyc

# Ignore the build directories but only directly under the project
# directories.
!/*/build/
"""
        spec = pathspec.PathSpec.from_lines(pathspec.patterns.GitWildMatchPattern, spec_text.splitlines())
        


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testBasic']
    unittest.main()