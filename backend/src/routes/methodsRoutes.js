const express = require("express");
const router = express.Router();

const {
    getAllMethods, 
    getMethodParameters,
    getAllMethodAndParameters,
    createMethod,
    updateMethod,
    deleteMethod
} = require("../controllers/methodsController");

router.get("/", getAllMethods);
router.get("/all-method-and-parameters", getAllMethodAndParameters);
router.get("/:id/parameters", getMethodParameters);
router.post("/", createMethod);
router.put("/:id", updateMethod);
router.delete("/:id", deleteMethod);

module.exports = router;