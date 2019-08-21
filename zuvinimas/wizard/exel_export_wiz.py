# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo import exceptions
import pytz
from dateutil.relativedelta import relativedelta
import datetime
import xlwt
from xlsxwriter.workbook import Workbook
from io import BytesIO
import base64

def prynt(print_me):
    import sys
    print(print_me)
    sys.stdout.flush()


class exel_export_wiz(models.TransientModel):
    _name = 'exel.export.wiz'
    _description = "Wizard: Quick Excel Export"

    def _compute_periods(self):
        releases_obj = self.env['zuvinimas.releases']
        releases_ids = releases_obj.search([])
        period_set = set(releases_ids.mapped(lambda r: r.date.year))
        period_list = list(map(lambda d: (d, d), period_set))
        return period_list
    
    period = fields.Selection(
        selection=lambda self: self._compute_periods(), string="Available Periods"
    )
    region_id = fields.Many2one("zuvinimas.regions", "Waterbody Region")
    water_body_id = fields.Many2one("zuvinimas.lakes", "Concerned Waterbody")
    species_id = fields.Many2one("zuvinimas.species", "Fish Species")
    age_group_id = fields.Many2one(
        "zuvinimas.species.age",
        "Fish Species Age Group",
        domain="['|', ('species_id', '=', species_id), ('base_age_group', '=', True)]"
    )
    group_by = fields.Selection(selection=[
            ('period', 'Period'),
            ('region_id', 'Region'),
            ('water_body_id', 'Waterbody'),
            ('species_id', 'Species'),
            ('age_group_id', 'Age'),
        ], string="Group By"
    )
    chart = fields.Selection(selection=[
            ('period', 'Period'),
            ('region_id', 'Region'),
            ('water_body_id', 'Waterbody'),
            ('species_id', 'Species'),
            ('age_group_id', 'Age'),
        ], string="Charts For"
    )
    ignore_date = fields.Boolean('Ignore Date When Sorting')
    file_name = fields.Char('Report Filename', size=64)
    excel_file = fields.Binary('Excel Report')
    
    @api.onchange(
        'period', 'region_id', 'water_body_id',
        'species_id', 'age_group_id', 'group_by', 'chart'
    )
    def _onchange_groupby(self):
        if self.group_by != False:
            if self.group_by == 'period' and self.period:
                self.group_by = False
            if self.group_by == 'region_id' and self.region_id:
                self.group_by = False
            if self.group_by == 'water_body_id' and self.water_body_id:
                self.group_by = False
            if self.group_by == 'species_id' and self.species_id:
                self.group_by = False
            if self.group_by == 'age_group_id' and self.age_group_id:
                self.group_by = False
        if self.chart != False:
            if self.group_by == self.chart:
                self.chart = False
            if self.chart == 'period' and self.period:
                self.chart = False
            if self.chart == 'region_id' and self.region_id:
                self.chart = False
            if self.chart == 'water_body_id' and self.water_body_id:
                self.chart = False
            if self.chart == 'species_id' and self.species_id:
                self.chart = False
            if self.chart == 'age_group_id' and self.age_group_id:
                self.chart = False
                
    @api.onchange('species_id')
    def _onchange_correct_age_groups(self):
        species_age_groups = self.env['zuvinimas.species.age'].search(
            ['|', ('species_id', '=', self.species_id.id), ('base_age_group', '=', True)]
        )
        if self.age_group_id not in species_age_groups:
            self.age_group_id = False
            
    def daterange_from_period(self, period):
        res = tuple()
        one_day = relativedelta(days=1)
        one_year = relativedelta(years=1)
        date_start_obj = datetime.date(int(period), 1, 1)
        date_finish_obj = date_start_obj + one_year - one_day
        res = (date_start_obj, date_finish_obj)
        
        return res
        
    def form_domain(self):
        domain = []
        if self.period:
            d_range = self.daterange_from_period(self.period)
            date_start_obj = d_range[0]
            date_finish_obj = d_range[1]
            domain.append(('date', '>=', fields.Date.to_string(date_start_obj)))
            domain.append(('date', '<=', fields.Date.to_string(date_finish_obj)))
        if self.region_id:
            domain.append(('region_id', '=', self.region_id.id))
        if self.water_body_id:
            domain.append(('water_body_id', '=', self.water_body_id.id))
        if self.species_id:
            domain.append(('species_id', '=', self.species_id.id))
        if self.age_group_id:
            domain.append(('age_group_id', '=', self.age_group_id.id))
        
        return domain
    
    def categorize(self, marker, records):
        report_data = {}
        group_categories = set()
        if marker != 'period':
            group_categories = list(map(lambda r: getattr(r, marker), records))
            report_data = self.group_by_categ_sheet(marker, records, group_categories, 'm2o')
        elif marker == 'period':
            group_categories = [p[0] for p in self._compute_periods()]
            group_categories = list(
                map(lambda p: self.daterange_from_period(p), group_categories)
            )
            report_data = self.group_by_categ_sheet(marker, records, group_categories, 'date')
            
        return report_data
    
    def group_by_categ_sheet(self, marker, records, categories, mode):
        res = {}
        if mode == 'm2o':
            for cat in sorted(categories, key=lambda c: c.name):
                res[cat.name] = list(filter(
                    lambda r: getattr(r, marker).id == cat.id, records
                ))
        elif mode == 'date':
            for cat in sorted(categories, key=lambda c: c[0]):
                res[cat[0].year] = list(filter(
                    lambda r: r.date >= cat[0] and r.date <= cat[1], records
                ))
                
        return res
    
    def get_width(self, string):
        string = str(string)
        num_characters = len(string)
        return float((num_characters) * 1.1)
    
    def xcell_write(self, worksheet, data, workbook, sheet):
        # Utility Datastore #######################################
        col_width = {}
        previous_values = {}
        indx_regions = {}
        indx_lakes = {}
        indx_species = {}
        indx_age_g = {}
        ## Various Styles #########################################
        style_header = workbook.add_format({
            'bold': True, 'font_size': 12, 'align': 'center', 'valign': 'center',
            'bg_color': 'yellow', 'bottom': 6
        })
        style_main = workbook.add_format({
            'font_size': 12, 'valign': 'center', 'bottom': 3
        })
        style_main_mid = workbook.add_format({
            'font_size': 12, 'align': 'center', 'valign': 'center', 'bottom': 3, 'left': 3
        })
        style_spec = workbook.add_format({
            'bold': True, 'font_size': 12, 'font_color': 'red', 'align': 'center',
            'valign': 'center', 'bg_color': 'yellow', 'bottom': 6
        })
        # Dynamic col width adjustment ################################
        def adj_width(col, value):
            if not col_width.get(col):
                col_width[col] = self.get_width(value)
                worksheet.set_column(col, col, col_width[col])
            elif self.get_width(value) > col_width[col]:
                col_width[col] = self.get_width(value)
                worksheet.set_column(col, col, col_width[col])
        ##############################################################
        def indexer(row, col, field, value, rec_id):
            previous_values[fld] = value
            previous_values['last_row'] = row
            previous_values['last_col'] = col
        # Sorted Fields ############################################################################
        report_fields = [
            'date', 'region_id', 'water_body_id', 'species_id', 'age_group_id', 'quantity'
        ]
        m2o = ['region_id', 'water_body_id', 'species_id', 'age_group_id']
        monitor_fields = list(report_fields[:-1])
        # Create Header ############################################################################
        releases_model = self.env['zuvinimas.releases']
        releases_tr_dict = self.env['ir.translation'].get_field_string(releases_model._name)
        for col_h, field in enumerate(report_fields):
            h_label = releases_tr_dict[field]
            adj_width(col_h, h_label)
            worksheet.set_row(0, 20)
            worksheet.write(0, col_h, h_label, style_header)
        ############################################################################################
        sorted_data = []
        if self.ignore_date:
            sorted_data = sorted(
                data, key=lambda r: (
                    r.region_id.name, r.water_body_id.name,
                    r.species_id.name, r.age_group_id.age
                )
            )
        else:
            sorted_data = sorted(
                data, key=lambda r: (
                    r.date.year, r.region_id.name, r.water_body_id.name,
                    r.species_id.name, r.age_group_id.age
                )
            )
        for row, zuv in enumerate(sorted_data, 1):
            for col, fld in enumerate(report_fields):
                st = style_main
                value = ''
                if fld in m2o:
                    value = getattr(getattr(zuv, fld), 'name')
                elif fld == 'date':
                    value = getattr(zuv, fld).year
                else:
                    st = style_main_mid
                    value = getattr(zuv, fld)
                indexer(row, col, fld, value, zuv.id)
                adj_width(col, value)
                worksheet.write(row, col, value, st)
        sheet_sum = sum(list(map(lambda z: z.quantity, sorted_data)))
        # Add Sheet total
        if sorted_data:
            worksheet.set_row(previous_values['last_row'] + 1, 20)
            worksheet.write(
                previous_values['last_row'] + 1, previous_values['last_col'] - 1,
                'SUM: ', style_spec
            )
            worksheet.write(
                previous_values['last_row'] + 1, previous_values['last_col'],
                sheet_sum, style_spec
            )
            # If chart is choosen, draw chart
            if self.chart:
                chart_data_all = self.categorize(self.chart, sorted_data)
                chart_data = list(map(
                    lambda i: (i[0], sum(list(map(lambda z: z.quantity, i[1])))),
                    chart_data_all.items()
                ))
                worksheet.write(
                        previous_values['last_row'] + 3, 0, "LABELS", style_header
                    )
                worksheet.write(
                        previous_values['last_row'] + 3, 1, "VALUES", style_header
                    )
                for nr, d_tuple in enumerate(chart_data, 1):
                    worksheet.write(
                        nr + previous_values['last_row'] + 3, 0, d_tuple[0], style_main
                    )
                    worksheet.write(
                        nr + previous_values['last_row'] + 3, 1, d_tuple[1], style_main
                    )
                chart = workbook.add_chart({'type': 'pie'})
                start_coord = previous_values['last_row'] + 4
                end_coord = len(chart_data) + previous_values['last_row'] + 3
                name = dict(self._fields['chart'].selection).get(self.chart) + " Chart"
                chart.add_series({
                    'categories': [str(sheet), start_coord, 0, end_coord, 0],
                    'values': [str(sheet), start_coord, 1, end_coord, 1],
                    'data_labels': {'value': True, 'series_name': True, 'percentage': True},
                    'name': name
                })
                chart_position = 'C' + str(start_coord)
                worksheet.insert_chart(chart_position, chart)
    
    def export(self):
        releases_obj = self.env['zuvinimas.releases']
        date = datetime.datetime.now(pytz.utc)
        filename = 'Zuvinimas_export_%s.xls' % date.date()
        if self.file_name:
            if self.file_name.endswith('.xls'):
                filename = self.file_name
            else:
                filename = self.file_name + '.xls'
        report_data = {}
        buff = BytesIO()
        workbook = Workbook(buff, {'in_memory': True})
        domain = self.form_domain()
        releases_ids = releases_obj.search(domain)
        if not releases_ids:
            raise exceptions.UserError(_('No Entries Found'))
        if self.group_by:
            report_data = self.categorize(self.group_by, releases_ids)
        else:
            report_data['all_data'] = releases_ids
        # Actual writing of data to excell
        for sheet, data in report_data.items():
            worksheet = workbook.add_worksheet(str(sheet))
            self.xcell_write(worksheet, data, workbook, sheet)
        workbook.close()
        self.excel_file = base64.encodestring(buff.getvalue())
        self.file_name = filename
        buff.close()
            
        return {
            'view_mode': 'form',
            'res_id': self.id,
            'res_model': 'exel.export.wiz',
            'view_type': 'form',
            "view_id": self.env.ref("zuvinimas.excel_export_wiz_result_form_view").id,
            'type': 'ir.actions.act_window',
            'target': 'new',
       }
       
    def save_rep(self):
        f_name = False
        field = 'excel_file'
        f_name = self.file_name
        url = '/web/content/%s/%s/%s/%s?download=true' % (self._name, self.id, field, f_name)
        return {
            'type': 'ir.actions.act_url',
            'name': 'contract',
            'url': url,
        }
