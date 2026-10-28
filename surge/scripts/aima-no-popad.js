/**
 * 爱玛出行（aima_travel）开屏弹窗广告 —— 改写响应，关掉弹窗
 *
 * 依据（2026-10-28 实机抓包，ProxyPin HAR）：
 *   GET https://app.aimaiot.cn/veh/vehicle/getVehCommonConfig
 *   响应 data 内含：
 *     "popAdMode": 1     ← 弹窗广告总开关（1 = 弹，0 = 不弹）
 *     "popAdTime": 8     ← 弹窗时长（秒）
 *     "blindBoxEnable": true  ← 盲盒营销位
 *
 * 为什么是「改写」而不是「拦截」：
 *   该接口是 App 启动链路的必需配置接口，直接 REJECT 会让 App 报
 *   「网络连接异常」（已实测）。改写则保持 200 + 原结构，仅把开关置 0，
 *   App 侧以为服务端关了广告，功能不受影响。
 *
 * 边界：只动这三个字段；JSON 解析失败时原样放行，绝不制造新故障。
 */

let body = $response.body;
try {
  const o = JSON.parse(body);
  if (o && o.data) {
    o.data.popAdMode = 0;
    o.data.popAdTime = 0;
    if ('blindBoxEnable' in o.data) o.data.blindBoxEnable = false;
  }
  body = JSON.stringify(o);
} catch (e) {
  // 结构变了就放行原始响应 —— 宁可弹窗，不可白屏
}
$done({ body });
