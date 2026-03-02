import axios from 'axios';

const client = axios.create({ baseURL: '' });

export function fetchNews(count = 50) {
  return client.get('/api/news', { params: { count } }).then((res) => res.data);
}

export function analyzeUrl(url) {
  return client.post('/api/analyze', { url }).then((res) => res.data);
}
