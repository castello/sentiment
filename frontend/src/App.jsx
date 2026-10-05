import { useState } from 'react';
import { ConfigProvider, Tabs, Typography, message } from 'antd';
import koKR from 'antd/locale/ko_KR';
import { analyzeUrl, analyzeText } from './api/client';
import NewsList from './components/NewsList';
import UrlInput from './components/UrlInput';
import TextInput from './components/TextInput';
import AnalysisResult from './components/AnalysisResult';
import './App.css';

const { Title } = Typography;

export default function App() {
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleAnalyze = async (url) => {
    setLoading(true);
    setResult(null);
    try {
      const data = await analyzeUrl(url);
      setResult(data);
    } catch (err) {
      const detail = err.response?.data?.detail || err.message;
      message.error(`분석 실패: ${detail}`);
    } finally {
      setLoading(false);
    }
  };

  const handleAnalyzeText = async (text) => {
    setLoading(true);
    setResult(null);
    try {
      const data = await analyzeText(text);
      setResult(data);
    } catch (err) {
      const detail = err.response?.data?.detail || err.message;
      message.error(`분석 실패: ${detail}`);
    } finally {
      setLoading(false);
    }
  };

  const items = [
    {
      key: 'news',
      label: '최신 뉴스',
      children: <NewsList onAnalyze={handleAnalyze} loading={loading} />,
    },
    {
      key: 'url',
      label: 'URL 직접 입력',
      children: <UrlInput onAnalyze={handleAnalyze} loading={loading} />,
    },
    {
      key: 'text',
      label: '텍스트 직접 입력',
      children: <TextInput onAnalyze={handleAnalyzeText} loading={loading} />,
    },
  ];

  return (
    <ConfigProvider locale={koKR}>
      <div className="app-container">
        <Title level={2} className="app-title">
          뉴스 기사 감성분석
        </Title>
        <Tabs items={items} />
        {(result || loading) && (
          <div className="analysis-section">
            <AnalysisResult result={result} loading={loading} />
          </div>
        )}
      </div>
    </ConfigProvider>
  );
}
