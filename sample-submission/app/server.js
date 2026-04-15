const express = require("express");
const fs = require("fs");
const path = require("path");

const app = express();
const port = 8080;

app.get("/", (req, res) => {
  const page = req.query.page || "home.html";
  const target = path.join(__dirname, "pages", page);
  try {
    const content = fs.readFileSync(target, "utf-8");
    res.status(200).send(content);
  } catch (error) {
    res.status(404).send("page not found");
  }
});

app.listen(port, "0.0.0.0", () => {
  console.log(`server listening on ${port}`);
});
