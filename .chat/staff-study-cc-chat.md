# Chat for StaffDiscount 

## L1 分析

读vendor/staffdiscount/api的back-end开发，High Level 分析此back-end API提供的功能，和数据关系。可以使用mermaid画出数据关系图，功能关系图，流程图等，图中的节点用一般文字即可，不要出现'()','[]'。最后结果存放在ana-staff/staff-L1-analysis.md

## L2 分析

### 管理后台
读取@ana-staff/staff-L1-analysis.md,分析 @vendor/staffdiscount/api 下的和后台管理相关的API，分析API具体实现。可以使用mermaid画出数据关系图，功能关系图，流程图等。最后结果存放到ana-staff/staff-L2-DiscountManager-analysis.md

读取@ana-staff/staff-L1-analysis.md,分析 @vendor/staffdiscount/api 下的和后台管理相关的API，分析API具体实现。可以使用mermaid画出数据关系图，功能关系图，流程图等。最后结果存放到ana-staff/staff-L2-UserManager-analysis.md

### 小程序
读取@ana-staff/staff-L1-analysis.md,分析 @vendor/staffdiscount/api 下的和小程序相关的API，分析API具体实现。可以使用mermaid画出数据关系图，功能关系图，流程图等。最后结果存放到ana-staff/staff-L2-miniApp-analysis.md

### 技术栈研究
基于.chat/staff-app-summary.md提到的技术栈，我现在希望将单体SpringBoot App改为Serverless的应用，采用TS编写，帮我研文件中提到的技术栈要怎么转变。将变更后的技术栈和技术使用方案写入 spec/staff-app/technical-stack.md