// src/services/photoService.js
const API_BASE_URL = 'http://localhost:5000/api';

export const photoService = {
  // Get all photos from Flask backend
  fetchPhotos: async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/photos`);
      const data = await response.json();
      
      if (data.success) {
        // Transform Flask response to match your component's expected format
        return data.photos.map(photo => ({
          id: photo.filename,
          file_path: photo.filename,  // Store filename for URL generation
          image_url: `${API_BASE_URL}/photos/${photo.filename}`,  // Full URL to access photo
          user_name: photo.card_uid === 'unknown' ? 'Unknown User' : `Card: ${photo.card_uid.substring(0, 8)}...`,
          date: photo.created_date,
          time: photo.created_time_str,
          status: 'APPROVED',  // Since these are from successful PPE checks
          card_uid: photo.card_uid,
          timestamp: photo.created_time
        }));
      }
      return [];
    } catch (error) {
      console.error('Error fetching photos:', error);
      return [];
    }
  },

  // Get single photo URL
  getPhotoUrl: (filename) => {
    return `${API_BASE_URL}/photos/${filename}`;
  }
};