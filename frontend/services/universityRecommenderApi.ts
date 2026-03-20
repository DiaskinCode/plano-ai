import api from "./api";

// University Profile API
export const universityProfileAPI = {
  // Get or create profile
  getProfile: () => api.get("/university-profile/profile/"),

  // Create new profile
  createProfile: (data: any) =>
    api.post("/university-profile/profile/create/", data),

  // Update profile
  updateProfile: (data: any) => api.patch("/university-profile/profile/", data),

  // Delete profile
  deleteProfile: () => api.delete("/university-profile/profile/delete/"),

  // Get completion status
  getCompletion: () => api.get("/university-profile/profile/completion/"),

  // Extracurricular activities
  getExtracurriculars: () =>
    api.get("/university-profile/profile/extracurriculars/"),
  addExtracurricular: (data: any) =>
    api.post("/university-profile/profile/extracurriculars/", data),
  updateExtracurricular: (id: number, data: any) =>
    api.patch(`/university-profile/profile/extracurriculars/${id}/`, data),
  deleteExtracurricular: (id: number) =>
    api.delete(`/university-profile/profile/extracurriculars/${id}/`),
};

// University Recommender API
export const universityRecommenderAPI = {
  // Generate recommendations
  generateRecommendations: (useLLM: boolean = true, profileData?: any) =>
    api.post("/university-recommender/recommend/generate/", {
      use_llm: useLLM,
      ...profileData,
    }, {
      timeout: 60000, // 60 second timeout
    }),

  // Submit feedback
  submitFeedback: (
    itemId: number,
    action: string,
    newBucket?: string,
    notes?: string,
  ) =>
    api.post("/university-recommender/feedback/", {
      item_id: itemId,
      action,
      new_bucket: newBucket,
      notes,
    }),

  // Shortlist management
  getShortlist: () => api.get("/university-recommender/shortlist/"),
  addToShortlist: (shortName: string, notes?: string) =>
    api.post("/university-recommender/shortlist/", {
      short_name: shortName,
      notes,
    }),
  removeFromShortlist: (shortName: string) =>
    api.delete("/university-recommender/shortlist/remove/", {
      data: { short_name: shortName },
    }),

  // University search
  searchUniversities: (query: string, country?: string) =>
    api.get("/university-recommender/universities/search/", {
      params: { q: query, country },
    }),

  // Analytics (admin only)
  getAnalytics: (days: number = 30) =>
    api.get("/university-recommender/analytics/", { params: { days } }),

  // Featured universities for home page
  getFeatured: () => api.get("/universities/featured/"),
};

export default {
  universityProfile: universityProfileAPI,
  universityRecommender: universityRecommenderAPI,
};
