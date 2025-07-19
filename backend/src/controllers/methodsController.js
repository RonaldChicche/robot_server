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

exports.getAllMethodsAndParameters = async (req, res) => {
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
        ORDER BY m.id, p.param_order;`
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


exports.getMethodParameters = async (req, res) => {
  const methodId = req.params.methodId;

  try {
    const result = await pool.query(
      `SELECT id, name, type, required, default_value, group_name, param_order
      FROM parameters
      WHERE method_id = $1
      ORDER BY COALESCE(param_order, 0)`,
      [methodId]
    );

    res.json(result.rows);
  } catch (err) {
    console.error("❌ Error al obtener parámetros:", err);
    res.status(500).json({ error: "Error interno" });
  }
};


exports.createParameter = async (req, res) => {
  const { methodId } = req.params.methodId;
  const { name, type, required, default_value, group_name, param_order } = req.body;

  try {
    await pool.query(
      "INSERT INTO parameters (method_id, name, type, required, default_value, group_name, param_order) VALUES ($1, $2, $3, $4, $5, $6, $7)",
      [methodId, name, type, required, default_value, group_name, param_order]
    );
    res.status(201).json({ success: true, message: "Parámetro creado exitosamente" });
  } catch (err) {
    console.error("❌ Error al crear parámetro:", err);
    res.status(500).json({ error: "Error interno" });
  }
};

exports.updateParameter = async (req, res) => {
  const paramId = req.params.paramId;
  const { name, type, required, default_value, group_name, param_order } = req.body;  

  try {
    await pool.query(
      "UPDATE parameters SET name = $1, type = $2, required = $3, default_value = $4, group_name = $5, param_order = $6 WHERE id = $7",
      [name, type, required, default_value, group_name, param_order, paramId]
    );
    res.status(200).json({ success: true, message: "Parámetro actualizado exitosamente" });
  } catch (err) {
    console.error("❌ Error al actualizar parámetro:", err);
    res.status(500).json({ error: "Error interno" });
  }
};

exports.deleteParameter = async (req, res) => {
    const paramId = req.params.paramId;
  
    try {
      await pool.query("DELETE FROM parameters WHERE id = $1", [paramId]);
      res.status(200).json({ success: true, message: "Parámetro eliminado exitosamente" });
    } catch (err) {
      console.error("❌ Error al eliminar parámetro:", err);
      res.status(500).json({ error: "Error interno" });
    }
  }
