from odoo import api, fields, models

class HrContract(models.Model):
    _inherit = "hr.contract"

    client_id = fields.Many2one("res.partner", string="Client")
    project_id = fields.Many2one("project.project", string="Projet")
    collaborator_ids = fields.One2many('project.collaborator', 'contract_id', string='Collaborators', copy=False)
    wage = fields.Monetary('Wage', required=False, tracking=True, help="Employee's monthly gross wage.", group_operator="avg")

