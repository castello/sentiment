import { useState } from 'react';
import { Button, Input } from 'antd';

const { TextArea } = Input;

export default function TextInput({ onAnalyze, loading }) {
  const [text, setText] = useState('');

  const handleSubmit = () => {
    const trimmed = text.trim();
    if (trimmed) {
      onAnalyze(trimmed);
    }
  };

  return (
    <div style={{ maxWidth: 700 }}>
      <TextArea
        placeholder="분석할 텍스트를 입력하세요 (리뷰, SNS 글 등)"
        value={text}
        onChange={(e) => setText(e.target.value)}
        rows={6}
        allowClear
        style={{ marginBottom: 12 }}
      />
      <Button type="primary" loading={loading} onClick={handleSubmit}>
        분석 시작
      </Button>
    </div>
  );
}
