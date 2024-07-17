from odoo import fields, models, api

class projectCollaborateurs(models.Model):
    _inherit = 'project.collaborator'

    employee_id = fields.Many2one('hr.employee')
    contrat_id = fields.Many2one('hr.contract', compute="computeContart_id")
    start_date = fields.Date()
    end_date = fields.Date()
    tx_sale = fields.Float()
    tx_buy = fields.Float()
    partner_id = fields.Many2one('res.partner', 'Collaborator', required=False, readonly=True)

    @api.depends("employee_id")
    def computeContart_id(self):
        """hr.contract"""
        contrat_ids = self.env['hr.contract'].search([('employee_id', '=', self.employee_id.id)])
        if not contrat_ids: self.contrat_id = None
        contrat_id = None
        for contrat in contrat_ids:
            if contrat.state != 'open': continue
            contrat_id = contrat.id
        if not contrat_id: self.contrat_id = None
        self.contrat_id = contrat_id
        # return contrat_id

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