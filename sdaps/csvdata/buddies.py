# -*- coding: utf-8 -*-
# SDAPS - Scripts for data acquisition with paper based surveys
# Copyright(C) 2008, Christoph Simon <post@christoph-simon.eu>
# Copyright(C) 2008, Benjamin Berg <benjamin@sipsolutions.net>
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

import csv

from sdaps import model

import os
import os.path

class Questionnaire(model.buddy.Buddy):

    __metaclass__ = model.buddy.Register
    name = 'csvdata'
    obj_class = model.questionnaire.Questionnaire

    def open_csv(self, csvfile, image_writer=None, export_images=False, export_question_images=False, export_quality=False, csv_options={}):
        header = ['questionnaire_id', 'global_id']

        self.export_quality = export_quality

        self.image_writer = image_writer
        if image_writer is not None and (export_images or export_question_images):
            from sdaps.utils.image import ImageWriter

            self.export_images = export_images
            self.export_question_images = export_question_images

        else:
            self.export_images = None
            self.export_question_images = None

        for qobject in self.obj.qobjects:
            header.extend(qobject.csvdata.export_header())
        self.file = csvfile
        self.csv = csv.DictWriter(self.file, header, **csv_options)
        self.csv.writerow({value: value for value in header})

    def export_data(self):
        data = {'questionnaire_id': unicode(self.obj.sheet.questionnaire_id),
            'global_id': unicode(self.obj.sheet.global_id)}
        for qobject in self.obj.qobjects:
            data.update(qobject.csvdata.export_data())
        self.csv.writerow(data)

    def export_finish(self):
        del self.csv

    def import_data(self, data):
        try:
            self.obj.survey.goto_questionnaire_id(data['questionnaire_id'])
        except ValueError:
            # The sheet does not exist
            # Ignore it
            pass
        else:
            for qobject in self.obj.qobjects:
                qobject.csvdata.import_data(data)


class QObject(model.buddy.Buddy):

    __metaclass__ = model.buddy.Register
    name = 'csvdata'
    obj_class = model.questionnaire.QObject

    def export_header(self):
        if self.obj.questionnaire.csvdata.export_question_images:
            return [self.obj.id_csv(self.obj.id) + '_image']
        else:
            return []

    def export_data(self):
        data = {}
        if self.obj.questionnaire.csvdata.export_question_images:
            if self.obj.boxes:
                img = self.obj.questionnaire.csvdata.image_writer.output_boxes(self.obj.boxes, real=False)
                data[self.obj.id_csv() + '_image'] = img

        return data

    def import_data(self, data):
        pass

class QHead(QObject):

    __metaclass__ = model.buddy.Register
    name = 'csvdata'
    obj_class = model.questionnaire.Head

    def export_header(self):
        return []

    def export_data(self):
        return {}

class Choice(QObject):

    __metaclass__ = model.buddy.Register
    name = 'csvdata'
    obj_class = model.questionnaire.Choice

    def export_header(self):
        header = QObject.export_header(self)
        for box in self.obj.boxes:
            header += box.csvdata.export_header()

        return header

    def export_data(self):
        data = QObject.export_data(self)

        for box in self.obj.boxes:
            data.update(box.csvdata.export_data())

        return data

    def import_data(self, data):
        for box in self.obj.boxes:
            if self.obj.id_csv(box.id) in data:
                box.csvdata.import_data(data[self.obj.id_csv(box.id)])

class Text(QObject):

    __metaclass__ = model.buddy.Register
    name = 'csvdata'
    obj_class = model.questionnaire.Text

    def export_header(self):
        header = QObject.export_header(self)
        for box in self.obj.boxes:
            header += box.csvdata.export_header()

        return header

    def export_data(self):
        data = QObject.export_data(self)

        for box in self.obj.boxes:
            data.update(box.csvdata.export_data())

        return data

    def import_data(self, data):
        for box in self.obj.boxes:
            if self.obj.id_csv(box.id) in data:
                box.csvdata.import_data(data[self.obj.id_csv(box.id)])

class Option(QObject):

    __metaclass__ = model.buddy.Register
    name = 'csvdata'
    obj_class = model.questionnaire.Option

    def export_header(self):
        header = QObject.export_header(self)
        header += [self.obj.id_csv()]
        return header

    def export_data(self):
        data = {self.obj.id_csv(): '%i' % self.obj.get_answer()}
        data.update(QObject.export_data(self))
        return data

    def import_data(self, data):
        if self.obj.id_csv() in data:
            self.obj.set_answer(int(data[self.obj.id_csv()]))


class Additional_Mark(model.buddy.Buddy):

    __metaclass__ = model.buddy.Register
    name = 'csvdata'
    obj_class = model.questionnaire.Additional_Mark

    def export_header(self):
        return [self.obj.id_csv()]

    def export_data(self):
        return {self.obj.id_csv(): '%i' % self.obj.get_answer()}

    def import_data(self, data):
        if self.obj.id_csv() in data:
            self.obj.set_answer(int(data[self.obj.id_csv()]))


class Box(model.buddy.Buddy):

    __metaclass__ = model.buddy.Register
    name = 'csvdata'
    obj_class = model.questionnaire.Box

    def export_header(self):
        header = [self.obj.id_csv()]
        if self.obj.question.questionnaire.csvdata.export_quality:
            header += [self.obj.id_csv() + '_quality']
        return header

    def export_data(self):
        data = {self.obj.id_csv() : str(int(self.obj.data.state))}
        if self.obj.question.questionnaire.csvdata.export_quality:
            data.update({self.obj.id_csv() + '_quality' : self.obj.data.quality})
        return data

    def import_data(self, data):
        self.obj.data.state = int(data)


class Textbox(Box):

    __metaclass__ = model.buddy.Register
    name = 'csvdata'
    obj_class = model.questionnaire.Textbox

    def export_header(self):
        header = [self.obj.id_csv()]
        return header

    def export_data(self):
        data = str(int(self.obj.data.state))

        image_writer = self.obj.question.questionnaire.csvdata.image_writer

        if self.obj.data.state and self.obj.data.text:
            data = self.obj.data.text.encode('utf-8')
        elif self.obj.data.state and self.obj.question.questionnaire.csvdata.export_images:
            data = image_writer.output_box(self.obj)

        data = { self.obj.id_csv() : data }

        return data

    def import_data(self, data):
        try:
            state = int(data)
            text = u''
        except ValueError:
            state = 1
            text = unicode(data)

        self.obj.data.state = state
        self.obj.data.text = text


