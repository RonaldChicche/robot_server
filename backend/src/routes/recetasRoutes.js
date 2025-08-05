const express = require("express");
const router = express.Router();
const recetasController = require("../controllers/recetasController");

router.get("/", recetasController.getAll);
router.get("/:id", recetasController.getOne);
router.post("/", recetasController.create);
router.put("/:id", recetasController.update);
router.delete("/:id", recetasController.remove);

module.exports = router;
