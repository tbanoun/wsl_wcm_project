from odoo import fields, models, api

class projectCollaborateurs(models.Model):
    _inherit = 'project.collaborator'
    _rec_name = 'employee_id'

    employee_id = fields.Many2one('hr.employee')
    contrat_id = fields.Many2one('hr.contract', compute="computeContart_id")
    start_date = fields.Date()
    end_date = fields.Date()
    tx_sale = fields.Float()
    tx_buy = fields.Float()
    partner_id = fields.Many2one('res.partner', 'Collaborator', required=False, readonly=True)
    contract_id = fields.Many2one('hr.contract')

    @api.depends("employee_id")
    def computeContart_id(self):
        """hr.contract"""
        for rec in self:
            contrat_ids = self.env['hr.contract'].search([('employee_id', '=', rec.employee_id.id)])
            if not contrat_ids: rec.contrat_id = None
            contrat_id = None
            for contrat in contrat_ids:
                if contrat.state != 'open': continue
                contrat_id = contrat.id
            if not contrat_id: rec.contrat_id = None
            rec.contrat_id = contrat_id

    def write(self, vals):
        res = super(projectCollaborateurs, self).write(vals)

        return res

    def create(self, vals_list):
        res = super(projectCollaborateurs, self).create(vals_list)
        print(f"\n\n {vals_list} \n\n")
        return res


class ProjectProject(models.Model):
    _inherit = 'project.project'

    cost_center = fields.Char("Centre de coût")
    purchase_order = fields.Char("Bon de commande")
    contract_number = fields.Char("N° de contrat")
    sales_deadline = fields.Many2one('account.payment.term', string="Échéance de vente")
    purchase_deadline = fields.Many2one('account.payment.term', string="Échéance d'achat")

    @api.depends('collaborator_ids', 'privacy_visibility')
    def _compute_collaborator_count(self):
        """
        overwrite function calculate colaborateur
        """
        project_sharings = self.filtered(lambda project: project.privacy_visibility == 'portal')
        collaborator_read_group = self.env['project.collaborator']._read_group(
            [('project_id', 'in', project_sharings.ids), ('employee_id', '=', False)],
            ['project_id'],
            ['__count'],
        )
        collaborator_count_by_project = {project.id: count for project, count in collaborator_read_group}
        for project in self:
            project.collaborator_count = collaborator_count_by_project.get(project.id, 0)

    def openColaboratorView(self):
        """open intercontrat"""
        action = self.env['ir.actions.act_window']._for_xml_id('project.project_collaborator_action')
        action["domain"] = [('project_id', '=', self.id), ('employee_id', '=', False)]
        return action


    def openTimeshhetProject(self):
        """open timeshhet project"""
        action = self.env['ir.actions.act_window']._for_xml_id('hr_timesheet.act_hr_timesheet_line')
        action["domain"] = [('project_id', '=', self.id)]
        action["context"] = {'default_project_id': self.id}
        return action

    def get_contractType(self, type):
        """get id conract type if he exist else create it and return id """
        if type == 'sales':
            type_id = self.env['hr.contract.type'].sudo().search([('code', '=', 'c_sales')])
            if type_id: return type_id[0].id
            type_id = self.env['hr.contract.type'].sudo().create({
                'name': 'Contrat de vente',
                'code': 'c_sales'
            })
            return type_id.id
        elif type =='purchase':
            type_id = self.env['hr.contract.type'].sudo().search([('code', '=', 'c_purchase')])
            if type_id: return type_id[0].id
            type_id = self.env['hr.contract.type'].sudo().create({
                'name': 'Contrat d\'achat',
                'code': 'c_purchase'
            })
            return type_id.id
        return None

    def openContratSale(self):
        """open contrat"""
        conrat_type = self.get_contractType('sales')
        action = self.env['ir.actions.act_window']._for_xml_id('wsl_wcm_project.hr_contract_project_action')
        action["domain"] = [('project_id', '=', self.id), ('contract_type_id', '=', conrat_type)]
        action["context"] = {
            'tree_view_ref': 'wsl_wcm_project.project_contract_tree',
            'form_view_ref': 'wsl_wcm_project.project_contract_form',
            'default_project_id': self.id,
            'default_contract_type_id': conrat_type
            }
        return action

    def openContratPurshase(self):
        """open contrat"""
        conrat_type = self.get_contractType('purchase')
        action = self.env['ir.actions.act_window']._for_xml_id('wsl_wcm_project.hr_contract_project_action')
        action["domain"] = [('project_id', '=', self.id), ('contract_type_id', '=', conrat_type)]
        action["context"] = {
            'tree_view_ref': 'wsl_wcm_project.project_contract_tree',
            'form_view_ref': 'wsl_wcm_project.project_contract_form',
            'default_project_id': self.id,
            'default_contract_type_id': conrat_type
            }
        return action


class Employee(models.Model):
    _inherit = "hr.employee"

    def action_open_contract(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id('hr_contract.action_hr_contract')
        action['views'] = [(False, 'form')]
        action["context"] = {
            'tree_view_ref': 'hr_contract.hr_contract_view_tree',
            'form_view_ref': 'hr_contract.hr_contract_view_form'
        }
        if not self.contract_ids:
            action['context'] = {
                'default_employee_id': self.id,
            }
            action['target'] = 'new'
            return action

        target_contract = self.contract_id
        if target_contract:
            action['res_id'] = target_contract.id
            return action

        target_contract = self.contract_ids.filtered(lambda c: c.state == 'draft')
        if target_contract:
            action['res_id'] = target_contract[0].id
            return action

        action['res_id'] = self.contract_ids[0].id
        return action