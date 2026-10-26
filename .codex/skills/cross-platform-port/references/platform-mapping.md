# Android ↔ iOS 语义映射检查表

把下表当作检查问题，不当成一对一替换规则。实际方案依据目标架构、最低系统版本和验证过的 SDK 文档。适用于 Compose/XML 与 SwiftUI/UIKit，反向迁移同样检查。

| 源能力 | 跨端必须明确的语义 | 常见风险 |
|---|---|---|
| Activity/Fragment、UIViewController/Scene | 页面所有权、进入/离开、销毁、配置变化与进程重建、导航状态恢复 | 生命周期回调机械对照导致漏事件或重复加载 |
| ViewModel、SwiftUI 状态/Observation/ObservableObject | 状态实例归属、视图身份、保留时长、可观察粒度、目标系统可用性 | 页面重建丢状态；强制升级目标框架 |
| Coroutine/Task、Flow/Combine/AsyncSequence | 初值、共享、重放、背压、取消、异常、执行上下文、UI隔离 | 热/冷流不等价；更新 UI 不在正确隔离域 |
| EventBus/Notification/事件发布 | sticky/replay、订阅时机、一次性消费、进程范围、并发顺序 | 后台事件丢失、重复导航和生命周期泄漏 |
| 返回栈/Navigation/深链 | 参数、返回结果、交互返回、取消、重复入口、恢复 | Android 返回键与 iOS 返回手势被错误禁用或重复处理 |
| SharedPreferences/DataStore/UserDefaults | 原子性、类型、默认值、同步时序、迁移 | 把凭据存在普通偏好存储 |
| Keystore/Keychain | 安全模型、可用时机、安装/卸载与备份、加密与访问控制 | 密钥不可直接跨平台复制，不读取私钥 |
| Room/SQLite/Core Data/其他数据库 | schema、事务、线程、迁移、关系、兼容与查询语义 | 库名相似不代表数据库文件兼容 |
| HTTP/JSON/日期/数值 | null/缺省、未知字段、整数范围、金额精度、时区、重试幂等性、认证、缓存 | Double 精度、默认值与解码行为变化 |
| RecyclerView/Lazy列表/UICollectionView/List | 稳定标识、复用、分页、滚动位置、刷新、占位与性能 | item identity变化导致状态错绑或滚动跳动 |
| 图片/字体/图标/资源 | 密度、矢量能力、裁切、字体授权与fallback、资源目标引用 | SVG/vector不直接兼容；数字相同视觉不同 |
| 权限/通知/推送 | 授权时机、拒绝/永久拒绝、能力配置、设备令牌、返回设置页 | 权限列表不能按名称照搬 |
| 后台任务/定位/音视频 | 平台执行限制、激活条件、时限、恢复、前后台切换 | iOS 不承诺 Android 式常驻执行 |
| 支付/账号/第三方SDK | 官方目标 SDK、服务配置、回调、外部跳转、错误和用户可见差异 | 不存在的 SDK、空支付成功回调、签名配置遗漏 |
| ARC/GC/闭包/回调 | 引用所有权、循环引用、资源释放、观察者注销 | Swift 强引用环、协程或listener超出页面寿命 |
| 构建/工程集成 | Gradle variants、Xcode targets/schemes、SPM/Pods、资源/entitlements、最低系统 | 文件已生成但未加入正确 target；未批准依赖升级 |

## 差异分类

- `strict`：相关可观察行为已设计为严格等价；仍需要测试证明。
- `native-substitute`：目标采用原生替代，明确交互/视觉/能力差异，用户批准。
- `partial`：只支持部分范围，明确缺失、用户影响、临时措施；关键项保持阻塞。
- `unsupported`：没有可用实现，明确原因和替代方案；不能标成已迁移。

默认首版仅将 strict/native-substitute 纳入 ready。partial/unsupported 必须先返回规格阶段，取得缩小范围或替代方案的明确确认并更新 IR/设计。不能仅改枚举掩盖实际未实现。

## 版本化知识积累

为真实通过的映射记录源/目标框架和 SDK 版本、适用条件、语义差异、证据与回归用例。只复用已验证样例；不把模型生成结果直接当知识库事实。每次升级框架或 SDK 重新验证相关映射。不要承诺 SwiftUI/UIKit、Compose/XML 与自定义渲染框架能无条件互换。
