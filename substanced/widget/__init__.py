import json

from colander import (
    Invalid,
    null,
)
from colander.iso8601 import ISO8601_REGEX

from deform import widget as deform_widget
from deform.i18n import _


class UserTimeZoneDateTimeInputWidget(deform_widget.DateTimeInputWidget):
    template = 'timezonedatetimeinput'

    def serialize(self, field, cstruct, **kw):
        if cstruct in (null, None):
            cstruct = ''
        readonly = kw.get('readonly', self.readonly)

        kw['timezone'] = ''
        if cstruct:
            parsed = ISO8601_REGEX.match(cstruct)
            if parsed: # strip timezone if it's there
                timezone = parsed.groupdict()['timezone']
                if timezone and cstruct.endswith(timezone):
                    cstruct = cstruct[:-len(timezone)]
                    kw['timezone'] = timezone

        try:
            date, time = cstruct.split('T', 1)
            try:
                # get rid of milliseconds
                time, _ = time.split('.', 1)
            except ValueError:
                pass
            kw['date'], kw['time'] = date, time
        except ValueError: # need more than one item to unpack
            kw['date'] = kw['time'] = ''


        date_options = dict(
            kw.get('date_options') or self.date_options or
            self.default_date_options
            )
        date_options['formatSubmit'] = 'yyyy-mm-dd'
        kw['date_options_json'] = json.dumps(date_options)

        time_options = dict(
            kw.get('time_options') or self.time_options or
            self.default_time_options
            )
        time_options['formatSubmit'] = 'HH:i'
        kw['time_options_json'] = json.dumps(time_options)

        values = self.get_template_values(field, cstruct, kw)
        template = readonly and self.readonly_template or self.template
        return field.renderer(template, **values)

    def deserialize(self, field, pstruct):
        if pstruct is null:
            return null
        else:
            # seriously pickadate?  oh.  right.  i forgot.  you're javascript.
            date = pstruct['date'].strip()
            time = pstruct['time'].strip()
            timezone = pstruct['timezone'].strip()
            date_submit = pstruct['date_submit'].strip()
            time_submit = pstruct['time_submit'].strip()

            date = date_submit or date
            time = time_submit or time

            if (not time and not date and not timezone):
                return null

            result = 'T'.join([date, time]) + timezone

            if not date:
                raise Invalid(field.schema, _('Incomplete date'), result)

            if not time:
                raise Invalid(field.schema, _('Incomplete time'), result)

            if not timezone:
                raise Invalid(field.schema, _('Incomplete timezone'), result)

            return result
