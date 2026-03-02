import { Card, Col, Descriptions, Row, Spin, Statistic, Tag, Typography } from 'antd';
import SentimentChart from './SentimentChart';
import KeywordTable from './KeywordTable';
import SentenceTable from './SentenceTable';

const { Title } = Typography;

const OVERALL_COLOR = { '긍정': '#52c41a', '중립': '#faad14', '부정': '#f5222d' };

export default function AnalysisResult({ result, loading }) {
  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: 48 }}>
        <Spin size="large" tip="기사를 분석하고 있습니다..." />
      </div>
    );
  }

  if (!result) return null;

  const { title, summary, keywords, sentences } = result;

  return (
    <div>
      <Title level={4}>{title}</Title>

      <Row gutter={[16, 16]}>
        <Col xs={24} md={8}>
          <Card>
            <Statistic
              title="전체 감성"
              value={summary.overall}
              valueStyle={{ color: OVERALL_COLOR[summary.overall] }}
            />
            <Statistic
              title="총 문장 수"
              value={summary.total_sentences}
              style={{ marginTop: 16 }}
            />
          </Card>
        </Col>
        <Col xs={24} md={16}>
          <Card title="감성 비율">
            <SentimentChart ratios={summary.ratios} counts={summary.counts} />
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col xs={24} md={12}>
          <Card title="키워드 빈도수 Top 10" size="small">
            <KeywordTable
              data={keywords.frequency}
              valueKey="count"
              valueTitle="빈도수"
            />
          </Card>
        </Col>
        <Col xs={24} md={12}>
          <Card title="TF-IDF 핵심 키워드 Top 10" size="small">
            <KeywordTable
              data={keywords.tfidf}
              valueKey="score"
              valueTitle="TF-IDF 점수"
            />
          </Card>
        </Col>
      </Row>

      <Card title="문장별 분석 결과" style={{ marginTop: 16 }} size="small">
        <SentenceTable sentences={sentences} />
      </Card>
    </div>
  );
}
