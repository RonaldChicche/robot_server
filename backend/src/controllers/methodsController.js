const { pool } = require("../config/db");

exports.getAllMethods = async (req, res) => {
  try {
    const result = await pool.query("SELECT * FROM methods ORDER BY id");
    res.json(result.rows);
  } catch (err) {
    console.error("❌ Error al obtener métodos:", err);
    res.status(500).json({ error: "Error interno" });
  }
};

exports.getMethodParameters = async (req, res) => {
  const methodId = req.params.id;

  try {
    const result = await pool.query(
      `SELECT id, name, type, required, default_value, group_name, param_order
      FROM parameters
      WHERE method_id = $1
      ORDER BY id, COALESCE(param_order, 0)`,
      [methodId]
    );

    res.json(result.rows);
  } catch (err) {
    console.error("❌ Error al obtener parámetros:", err);
    res.status(500).json({ error: "Error interno" });
  }
};

exports.getAllMethodAndParameters = async (req, res) => {
  try {
    const result = await pool.query(
      `SELECT 
            m.id AS method_id, 
            m.name AS method_name, 
            m.description AS method_description,
            m.type, m.requires_params,
            p.id AS parameter_id, 
            p.name AS parameter_name, 
            p.type AS parameter_type, 
            p.required, 
            p.default_value
        FROM methods m
        LEFT JOIN parameters p ON m.id = p.method_id
        ORDER BY m.id, p.id;`
    );
    res.json(result.rows);
  } catch (err) {
    console.error("❌ Error al obtener métodos y parámetros:", err);
    res.status(500).json({ error: "Error interno" });
  }
};

exports.createMethod = async (req, res) => {
  const { name, type } = req.body;

  try {
    await pool.query(
      "INSERT INTO methods (name, type) VALUES ($1, $2)",
      [name, type]
    );
    res.status(201).json({ success: true, message: "Metodo creado exitosamente" });
  } catch (err) {
    console.error("❌ Error al crear metodo:", err);
    res.status(500).json({ error: "Error interno" });
  }
};  

exports.updateMethod = async (req, res) => {
  const methodId = req.params.id;
  const { name, type } = req.body;

  try {
    await pool.query(
      "UPDATE methods SET name = $1, type = $2 WHERE id = $3",
      [name, type, methodId]
    );
    res.status(200).json({ success: true, message: "Metodo actualizado exitosamente" });
  } catch (err) {
    console.error("❌ Error al actualizar metodo:", err);
    res.status(500).json({ error: "Error interno" });
  }
};

exports.deleteMethod = async (req, res) => {
  const methodId = req.params.id;

  try {
    await pool.query("DELETE FROM methods WHERE id = $1", [methodId]);
    res.status(200).json({ success: true, message: "Metodo eliminado exitosamente" });
  } catch (err) {
    console.error("❌ Error al eliminar metodo:", err);
    res.status(500).json({ error: "Error interno" });
  }
};

