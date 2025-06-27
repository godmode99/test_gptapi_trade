"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
const express_1 = __importDefault(require("express"));
const db_js_1 = require("./services/db.js");
const app = (0, express_1.default)();
app.use(express_1.default.json());
app.post('/signal', async (req, res) => {
    try {
        const result = await (0, db_js_1.insertSignal)(req.body);
        res.json(result);
    }
    catch (err) {
        console.error(err);
        res.status(500).json({ error: 'Failed to save signal' });
    }
});
app.post('/order', async (req, res) => {
    try {
        const result = await (0, db_js_1.insertOrder)(req.body);
        res.json(result);
    }
    catch (err) {
        console.error(err);
        res.status(500).json({ error: 'Failed to save order' });
    }
});
app.post('/trade', async (req, res) => {
    try {
        const result = await (0, db_js_1.insertTrade)(req.body);
        res.json(result);
    }
    catch (err) {
        console.error(err);
        res.status(500).json({ error: 'Failed to save trade' });
    }
});
app.post('/event', async (req, res) => {
    try {
        const result = await (0, db_js_1.insertEvent)(req.body);
        res.json(result);
    }
    catch (err) {
        console.error(err);
        res.status(500).json({ error: 'Failed to save event' });
    }
});
exports.default = app;
if (process.env.NODE_ENV !== 'test') {
    const port = process.env.PORT || 3000;
    app.listen(port, () => {
        console.log(`API server listening on port ${port}`);
    });
}
