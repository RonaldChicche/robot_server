const express = require("express");
const router = express.Router();
const alarmasController = require("../controllers/alarmasController");

router.get("/:codigo", alarmasController.getByCodigo);

module.exports = router;
