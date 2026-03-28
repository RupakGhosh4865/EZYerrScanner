const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000"

export async function generatePlan(file) {
  const formData = new FormData()
  formData.append("file", file)
  
  const response = await fetch(`${BASE_URL}/api/analyze/plan`, {
    method: "POST",
    body: formData
  })
  
  if (!response.ok) {
    const errorBody = await response.json().catch(() => ({ error: "Unknown error" }))
    throw new Error(errorBody.error || errorBody.detail || "Planning failed")
  }
  
  return response.json()
}

export async function executePlan(state) {
  const response = await fetch(`${BASE_URL}/api/analyze/execute`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(state)
  })
  
  if (!response.ok) {
    const errorBody = await response.json().catch(() => ({ error: "Unknown error" }))
    throw new Error(errorBody.error || errorBody.detail || "Execution failed")
  }
  
  return response.json()
}
