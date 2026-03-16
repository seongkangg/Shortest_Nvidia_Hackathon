// Vercel serverless: returns backend API URL from env (set in Vercel dashboard).
export default function handler(req, res) {
  res.setHeader("Access-Control-Allow-Origin", "*");
  res.setHeader("Cache-Control", "public, max-age=60");
  res.status(200).json({
    API: process.env.API_URL || "http://localhost:8000",
  });
}
