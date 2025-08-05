const { pool } = require("../config/db");

module.exports = {
  getByCodigo: async (req, res) => {
    const { codigo } = req.params;
    const result = await pool.query("SELECT * FROM alarmas WHERE codigo = $1", [codigo]);

    if (result.rowCount === 0) {
      return res.status(404).json({ error: "Alarma no encontrada" });
    }

    res.json(result.rows[0]);
  }
};
