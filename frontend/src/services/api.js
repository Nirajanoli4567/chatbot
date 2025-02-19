const API_BASE_URL = 'http://localhost:5003/api';

export const chatService = {
  sendMessage: async (message) => {
    try {
      const response = await fetch(`${API_BASE_URL}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({ message }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      console.log('API Response:', data);
      return data;
    } catch (error) {
      console.error('API Error:', error);
      throw error;
    }
  },

  getChatHistory: async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/chat-history`, {
        credentials: 'include'
      });
      return response.json();
    } catch (error) {
      console.error('Error fetching chat history:', error);
      throw error;
    }
  }
}; 