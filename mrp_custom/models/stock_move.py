from odoo import fields, models, api
from ..utils import utils


class StockMove(models.Model):
    _inherit = 'stock.move'

    @api.model
    def create(self, vals):
        res = super(StockMove, self).create(vals)
        for record in res:
            if record.raw_material_production_id:
                if record.product_id.bom_ids and record.product_id.generate_production \
                        or record.product_id.bom_ids and record.product_id.plan_production:
                    utils.generate_production(record,
                                              record.product_id,
                                              record.product_uom_qty,
                                              record.raw_material_production_id.picking_type_id.warehouse_id,
                                              record.raw_material_production_id.name,
                                              record.product_uom.id,
                                              record.raw_material_production_id.location_src_id.id)
        return res
