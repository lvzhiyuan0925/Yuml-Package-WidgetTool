📦 Yuml-Package-WidgetTool

为 Yuml 中的所有 widget 添加扩展功能模块。

⸻

✨ 功能一：sizeBox

为组件四个角添加调整按钮，模拟 UI 设计器中的大小调整行为。

🔧 说明：

在组件四个角自动添加 4 个小按钮。

支持通过鼠标拖动这些按钮实时调整组件尺寸。

✅ 使用方式：
```yuml
button1:
  sizeBox: ["button1_sizeBox", "button1"]
```

元素1为sizeBox变量名(全局), 元素2为button变量名
⸻

✨ 功能二：dragWidget

允许用户按住并拖动组件，改变其在窗口中的位置。

✅ 使用方式：
```yuml
button1:
  dragWidget: "button1"
```
拖动目标为 "button1" 本身。

⸻

💡 示例完整配置：
```yuml

windowCreated:
  button:
    button1:
      text: "Hello World"
      dragWidget: "button1"
      sizeBox: ["button1_sizeBox", "button1"]
      onMoved: moved
      show: true

moved:
  PythonScript: |
    button1_sizeBox.update_resize_buttons()

```
⸻

🛠️ 注意事项:

sizeBox 和 dragWidget 可独立使用，也可组合使用。

onMoved 用于监听组件位置变化（非拖动专用）。

⸻
