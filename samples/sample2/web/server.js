import express from "express";
import { readFile } from "fs";
import { join, dirname } from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const app = express();
const PORT = 8080;

function wrapTemplate(content) {
	return `
<!DOCTYPE html>
<html>
<head>
    <title>Corporate Intranet Portal</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 50px auto;
            padding: 20px;
            background-color: #f0f0f0;
        }
        .container {
            background-color: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        h1 {
            color: #333;
            border-bottom: 2px solid #007bff;
            padding-bottom: 10px;
        }
        nav {
            margin: 20px 0;
        }
        nav a {
            display: inline-block;
            margin-right: 15px;
            padding: 8px 16px;
            background-color: #007bff;
            color: white;
            text-decoration: none;
            border-radius: 4px;
        }
        nav a:hover {
            background-color: #0056b3;
        }
        .content {
            margin: 20px 0;
            line-height: 1.6;
        }
        .footer {
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            color: #666;
            font-size: 0.9em;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Corporate Intranet</h1>
        <nav>
            <a href="/?page=home.html">Home</a>
            <a href="/?page=about.html">About</a>
            <a href="/?page=contact.html">Contact</a>
        </nav>
        <div class="content">
            ${content}
        </div>
        <div class="footer">
            <p>© 2025 Corporate Intranet. Internal Use Only.</p>
        </div>
    </div>
</body>
</html>`;
}

app.get("/", (req, res) => {
	const page = req.query.page;

	if (!page) {
		return res.send(
			wrapTemplate(`
            <h2>Welcome</h2>
            <p>This is the internal portal for company employees.</p>
            <p>Use the navigation menu above to browse.</p>
        `),
		);
	}

	const filePath = join(__dirname, "pages", page);

	readFile(filePath, "utf8", (err, data) => {
		if (err) {
			res.status(404).send(
				wrapTemplate(`
                <h2>404 - Page Not Found</h2>
                <p>The requested page could not be found.</p>
                <p><strong>Error:</strong> ${err.message}</p>
                <p><strong>Attempted path:</strong> ${filePath}</p>
                <p><a href="/">Return to Home</a></p>
            `),
			);
		} else {
			res.send(wrapTemplate(data));
		}
	});
});

app.listen(PORT, "0.0.0.0", () => {
	console.log(`Corporate Intranet running on port ${PORT}`);
});
