const { pool } = require("../config/db");

// Validar datos
function validarReceta(data) {
  const campos = [
    "titulo", "long_caja", "ancho_caja", "altura_caja",
    "long_barra", "ancho_barra", "espesor", "peso"
  ];

  for (const campo of campos) {
    if (data[campo] === undefined || data[campo] === null || data[campo] <= 0) {
      throw new Error(`Campo inválido: ${campo}`);
    }
  }
}

module.exports = {
  getAll: async (req, res) => {
    const result = await pool.query("SELECT * FROM recetas ORDER BY id");
    res.json(result.rows);
  },

  getOne: async (req, res) => {
    const { id } = req.params;
    const result = await pool.query("SELECT * FROM recetas WHERE id = $1", [id]);
    if (result.rowCount === 0) return res.status(404).json({ error: "No encontrada" });
    res.json(result.rows[0]);
  },

  create: async (req, res) => {
    try {
      validarReceta(req.body);
      const {
        titulo, long_caja, ancho_caja, altura_caja,
        long_barra, ancho_barra, espesor, peso
      } = req.body;

      const result = await pool.query(`
        INSERT INTO recetas (titulo, long_caja, ancho_caja, altura_caja, long_barra, ancho_barra, espesor, peso)
        VALUES ($1,$2,$3,$4,$5,$6,$7,$8) RETURNING *
      `, [titulo, long_caja, ancho_caja, altura_caja, long_barra, ancho_barra, espesor, peso]);

      res.status(201).json(result.rows[0]);
    } catch (err) {
      res.status(400).json({ error: err.message });
    }
  },

  update: async (req, res) => {
    const { id } = req.params;
    try {
      validarReceta(req.body);
      const {
        titulo, long_caja, ancho_caja, altura_caja,
        long_barra, ancho_barra, espesor, peso
      } = req.body;

      const result = await pool.query(`
        UPDATE recetas SET
          titulo = $1,
          long_caja = $2,
          ancho_caja = $3,
          altura_caja = $4,
          long_barra = $5,
          ancho_barra = $6,
          espesor = $7,
          peso = $8
        WHERE id = $9 RETURNING *
      `, [titulo, long_caja, ancho_caja, altura_caja, long_barra, ancho_barra, espesor, peso, id]);

      if (result.rowCount === 0) return res.status(404).json({ error: "No encontrada" });
      res.json(result.rows[0]);
    } catch (err) {
      res.status(400).json({ error: err.message });
    }
  },

  remove: async (req, res) => {
    const { id } = req.params;
    const result = await pool.query("DELETE FROM recetas WHERE id = $1 RETURNING *", [id]);
    if (result.rowCount === 0) return res.status(404).json({ error: "No encontrada" });
    res.json({ message: "Receta eliminada", id });
  }
};
