import { useState } from 'react';
import { Button, Input, Space } from 'antd';

export default function UrlInput({ onAnalyze, loading }) {
  const [url, setUrl] = useState('');

  const handleSubmit = () => {
    const trimmed = url.trim();
    if (trimmed) {
      onAnalyze(trimmed);
    }
  };

  return (
    <Space.Compact style={{ width: '100%', maxWidth: 700 }}>
      <Input
        placeholder="뉴스 기사 URL을 입력하세요"
        value={url}
        onChange={(e) => setUrl(e.target.value)}
        onPressEnter={handleSubmit}
        allowClear
      />
      <Button type="primary" loading={loading} onClick={handleSubmit}>
        분석 시작
      </Button>
    </Space.Compact>
  );
}
