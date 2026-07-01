import { useEffect, useMemo, useRef, useState } from "react";
import {
  Button,
  Card,
  Form,
  Input,
  List,
  Select,
  Space,
  Typography,
  message,
} from "antd";
import {
  PauseCircleOutlined,
  RobotOutlined,
  SearchOutlined,
} from "@ant-design/icons";
import {
  getAiFundReportDetail,
  listAiFundReports,
  streamFundSummary,
  type AiFundReportListItem,
  type AiFundReportListRequest,
} from "../../api/ai";
import {
  listFavoriteFundOptions,
  type FavoriteFundOptionItem,
} from "../../api/fund";
import CherryMarkdownViewer from "../../components/CherryMarkdownViewer";

type AiFundAnalysisForm = {
  favorite_fund_code?: string;
  fund_code?: string;
};

function AiFundAnalysisPage() {
  const [messageApi, contextHolder] = message.useMessage();
  const [form] = Form.useForm<AiFundAnalysisForm>();
  const [favoriteOptions, setFavoriteOptions] = useState<
    FavoriteFundOptionItem[]
  >([]);
  const [favoriteLoading, setFavoriteLoading] = useState(true);
  const [reports, setReports] = useState<AiFundReportListItem[]>([]);
  const [reportsLoading, setReportsLoading] = useState(true);
  const [activeReportId, setActiveReportId] = useState<number>();
  const [content, setContent] = useState("");
  const [loading, setLoading] = useState(false);
  const abortControllerRef = useRef<AbortController | null>(null);

  useEffect(() => {
    listFavoriteFundOptions()
      .then(setFavoriteOptions)
      .catch(() => setFavoriteOptions([]))
      .finally(() => setFavoriteLoading(false));
  }, []);

  const loadReports = async (fundCode?: string, showLoading = true) => {
    if (showLoading) {
      setReportsLoading(true);
    }
    try {
      const request: AiFundReportListRequest = {
        fund_code: fundCode?.trim() || undefined,
        page: 1,
        page_size: 20,
      };
      const data = await listAiFundReports(request);
      setReports(data.items);
    } catch (error) {
      messageApi.error(
        error instanceof Error ? error.message : "历史报告加载失败",
      );
    } finally {
      setReportsLoading(false);
    }
  };

  useEffect(() => {
    listAiFundReports({
      page: 1,
      page_size: 20,
    })
      .then((data) => setReports(data.items))
      .catch(() => setReports([]))
      .finally(() => setReportsLoading(false));
  }, []);

  const favoriteSelectOptions = useMemo(
    () =>
      favoriteOptions.map((item) => ({
        label: `${item.fund_code} ${item.fund_name}${item.fund_type ? ` (${item.fund_type})` : ""}`,
        value: item.fund_code,
      })),
    [favoriteOptions],
  );

  const submit = async (values: AiFundAnalysisForm) => {
    const fundCode = (
      values.favorite_fund_code ||
      values.fund_code ||
      ""
    ).trim();
    if (!fundCode) {
      messageApi.warning("请选择自选基金或输入基金代码");
      return;
    }

    abortControllerRef.current?.abort();
    const abortController = new AbortController();
    abortControllerRef.current = abortController;
    setContent("");
    setActiveReportId(undefined);
    setLoading(true);

    try {
      await streamFundSummary(
        { fund_code: fundCode },
        {
          signal: abortController.signal,
          onMessage: (message) =>
            setContent((previous) => `${previous}${message}`),
          onDone: () => {
            setLoading(false);
            loadReports(fundCode);
          },
          onError: (error) => messageApi.error(error.message),
        },
      );
    } catch (error) {
      if (!abortController.signal.aborted) {
        messageApi.error(
          error instanceof Error ? error.message : "AI 分析失败",
        );
      }
    } finally {
      if (!abortController.signal.aborted) {
        setLoading(false);
      }
    }
  };

  const stop = () => {
    abortControllerRef.current?.abort();
    setLoading(false);
  };

  const openReport = async (report: AiFundReportListItem) => {
    setReportsLoading(true);
    try {
      const detail = await getAiFundReportDetail({ id: report.id });
      setContent(detail.content);
      setActiveReportId(detail.id);
      form.setFieldsValue({
        fund_code: detail.fund_code,
        favorite_fund_code: detail.fund_code,
      });
    } catch (error) {
      messageApi.error(
        error instanceof Error ? error.message : "报告详情加载失败",
      );
    } finally {
      setReportsLoading(false);
    }
  };

  return (
    <Card title="AI 基金分析" className="tool-panel">
      {contextHolder}
      <Form
        form={form}
        layout="inline"
        initialValues={{ favorite_fund_code: undefined, fund_code: "" }}
        onFinish={submit}
        className="query-form"
      >
        <Form.Item name="favorite_fund_code" label="我的自选">
          <Select
            allowClear
            showSearch
            className="favorite-fund-select"
            loading={favoriteLoading}
            placeholder="选择自选基金"
            optionFilterProp="label"
            options={favoriteSelectOptions}
            onChange={(fundCode?: string) => {
              if (fundCode) {
                form.setFieldValue("fund_code", fundCode);
              }
            }}
          />
        </Form.Item>
        <Form.Item name="fund_code" label="基金代码">
          <Input
            allowClear
            autoComplete="off"
            placeholder="不选自选时可手动输入"
          />
        </Form.Item>
        <Form.Item>
          <Space>
            <Button
              type="primary"
              icon={<SearchOutlined />}
              htmlType="submit"
              loading={loading}
            >
              开始分析
            </Button>
            <Button
              icon={<PauseCircleOutlined />}
              disabled={!loading}
              onClick={stop}
            >
              停止
            </Button>
          </Space>
        </Form.Item>
      </Form>

      <div className="ai-workspace">
        <div className="ai-result-panel">
          {content ? (
            <CherryMarkdownViewer value={content} />
          ) : (
            <div className="ai-empty-state">
              <RobotOutlined />
              <Typography.Text type="secondary">
                选择自选基金或输入基金代码后生成 AI 分析报告
              </Typography.Text>
            </div>
          )}
        </div>
        <Card size="small" title="历史报告" className="ai-history-panel">
          <List
            loading={reportsLoading}
            dataSource={reports}
            locale={{ emptyText: "暂无历史报告" }}
            renderItem={(item) => (
              <List.Item
                className={
                  activeReportId === item.id
                    ? "ai-history-item active"
                    : "ai-history-item"
                }
                onClick={() => openReport(item)}
              >
                <List.Item.Meta
                  title={item.fund_code}
                  description={new Date(item.created_at).toLocaleString()}
                />
              </List.Item>
            )}
          />
        </Card>
      </div>
    </Card>
  );
}

export default AiFundAnalysisPage;
