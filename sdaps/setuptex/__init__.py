# -*- coding: utf-8 -*-
# SDAPS - Scripts for data acquisition with paper based surveys
# Copyright(C) 2008, Christoph Simon <post@christoph-simon.eu>
# Copyright(C) 2010, Benjamin Berg <benjamin@sipsolutions.net>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

u"""
Contains the functionality to create a new SDAPS project using a LaTeX input
file.
"""

import sys
import os
import shutil
import glob

from sdaps.utils.mimetype import mimetype
from sdaps import model
from sdaps import log
from sdaps import paths
from sdaps import defs

from sdaps.utils import latex
from sdaps.utils.ugettext import ugettext, ungettext
_ = ugettext

from ..setup import buddies
from . import sdapsfileparser
from ..setup import additionalparser


def setup(survey, questionnaire_tex, additionalqobjects=None, extra_files=[]):
    if os.access(survey.path(), os.F_OK):
        log.error(_('The survey directory already exists.'))
        return 1

    mime = mimetype(questionnaire_tex)
    if mime != 'text/x-tex' and mime != '':
        log.warn(_('Unknown file type (%s). questionnaire_tex should be of type text/x-tex.') % mime)
        log.warn(_('Will keep going, but expect failure!'))

    if additionalqobjects is not None:
        mime = mimetype(additionalqobjects)
        if mime != 'text/plain' and mime != '':
            log.error(_('Unknown file type (%s). additionalqobjects should be text/plain.') % mime)
            return 1

    # Add the new questionnaire
    survey.add_questionnaire(model.questionnaire.Questionnaire())

    # Create the survey directory, and copy the tex file.
    os.makedirs(survey.path())
    try:
        shutil.copy(questionnaire_tex, survey.path('questionnaire.tex'))

        latex.write_override(survey, survey.path('sdaps.opt'), draft=True)

        # Copy class and dictionary files
        if paths.local_run:
            cls_files = os.path.join(paths.source_dir, 'tex', '*.cls')
            tex_files = os.path.join(paths.source_dir, 'tex', '*.tex')
            sty_files = os.path.join(paths.source_dir, 'tex', '*.sty')
            dict_files = os.path.join(paths.build_dir, 'tex', '*.dict')
        else:
            cls_files = os.path.join(paths.prefix, 'share', 'sdaps', 'tex', '*.cls')
            tex_files = os.path.join(paths.prefix, 'share', 'sdaps', 'tex', '*.tex')
            sty_files = os.path.join(paths.prefix, 'share', 'sdaps', 'tex', '*.sty')
            dict_files = os.path.join(paths.prefix, 'share', 'sdaps', 'tex', '*.dict')

        def copy_to_survey(files_glob):
            files = glob.glob(files_glob)
            for file in files:
                shutil.copyfile(file, survey.path(os.path.basename(file)))

        copy_to_survey(cls_files)
        copy_to_survey(tex_files)
        copy_to_survey(sty_files)
        copy_to_survey(dict_files)

        for add_file in extra_files:
            if os.path.isdir(add_file):
                shutil.copytree(add_file, survey.path(os.path.basename(add_file)))
            else:
                shutil.copyfile(add_file, survey.path(os.path.basename(add_file)))

        print _("Running %s now twice to generate the questionnaire.") % defs.latex_engine
        latex.compile('questionnaire.tex', cwd=survey.path())

        if not os.path.exists(survey.path('questionnaire.pdf')):
            print _("Error running \"%s\" to compile the LaTeX file.") % defs.latex_engine
            raise AssertionError('PDF file not generated')

        survey.defs.print_questionnaire_id = False
        survey.defs.print_survey_id = True

        # Parse qobjects
        try:
            sdapsfileparser.parse(survey)

            for qobject in survey.questionnaire.qobjects:
                qobject.setup.setup()
                qobject.setup.validate()

        except:
            log.error(_("Caught an Exception while parsing the SDAPS file. The current state is:"))
            print >>sys.stderr, unicode(survey.questionnaire)
            print >>sys.stderr, "------------------------------------"

            raise

        # Parse additionalqobjects
        if additionalqobjects:
            additionalparser.parse(survey, additionalqobjects)

        # Last but not least calculate the survey id
        survey.calculate_survey_id()

        if not survey.check_settings():
            log.error(_("Some combination of options and project properties do not work. Aborted Setup."))
            shutil.rmtree(survey.path())
            return 1

        # We need to now rebuild everything so that the correct ID is at the bottom
        # Dissable draft mode if the survey doesn't have questionnaire IDs
        latex.write_override(survey, survey.path('sdaps.opt'), draft=survey.defs.print_questionnaire_id)
        print _("Running %s now twice to generate the questionnaire.") % defs.latex_engine
        os.remove(survey.path('questionnaire.pdf'))
        latex.compile('questionnaire.tex', survey.path())

        if not os.path.exists(survey.path('questionnaire.pdf')):
            print _("Error running \"%s\" to compile the LaTeX file.") % defs.latex_engine
            raise AssertionError('PDF file not generated')

        # Print the result
        print survey.title

        for item in survey.info.items():
            print u'%s: %s' % item

        print unicode(survey.questionnaire)

        log.logfile.open(survey.path('log'))

        survey.save()
        log.logfile.close()
    except:
        log.error(_("An error occured in the setup routine. The survey directory still exists. You can for example check the questionnaire.log file for LaTeX compile errors."))
        raise
