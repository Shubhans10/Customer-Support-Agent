export const API_BASE_URL = "http://localhost:8000";

export async function fetchSkills() {
    const res = await fetch(`${API_BASE_URL}/api/skills`);
    if (!res.ok) throw new Error("Failed to fetch skills");
    return res.json();
}
