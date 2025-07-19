const express = require("express");
const router = express.Router();

const {
    getAllMethods, 
    getAllMethodsAndParameters,
    createMethod,
    updateMethod,
    deleteMethod,
    getMethodParameters,
    createParameter,
    updateParameter,
    deleteParameter
} = require("../controllers/methodsController");


router.get("/", getAllMethods); 
router.get("/all", getAllMethodsAndParameters); 
router.post("/", createMethod); 
router.put("/:id", updateMethod); 
router.delete("/:id", deleteMethod); 

router.get("/:methodId/parameters", getMethodParameters); 
router.post("/:methodId/parameters", createParameter); 
router.put("/parameters/:paramId", updateParameter); 
router.delete("/parameters/:paramId", deleteParameter); 

module.exports = router;