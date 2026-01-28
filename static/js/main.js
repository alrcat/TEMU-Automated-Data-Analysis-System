// 全局变量
let currentTable = '';

// 显示自动消失通知
function showNotification(message, type = 'success', duration = 3000) {
    const container = document.getElementById('notification-container');

    // 创建通知元素
    const notification = document.createElement('div');
    notification.className = `toast-notification ${type}`;
    notification.textContent = message;

    // 添加到容器
    container.appendChild(notification);

    // 触发显示动画
    setTimeout(() => {
        notification.classList.add('show');
    }, 10);

    // 设置自动消失（如果duration为0，则不自动消失）
    if (duration > 0) {
        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => {
                if (container.contains(notification)) {
                    container.removeChild(notification);
                }
            }, 300); // 等待动画完成后移除
        }, duration);
    }
}

// 清除所有通知
function clearNotifications() {
    const container = document.getElementById('notification-container');
    if (container) {
        container.innerHTML = '';
    }
}

// 页面加载时初始化
document.addEventListener('DOMContentLoaded', function() {
    currentTable = document.getElementById('current-table').textContent;
    loadConfig();
});

// 设置表名
async function setTable() {
    const tableInput = document.getElementById('table-input');
    const tableName = tableInput.value.trim();
    
    if (!tableName) {
        alert('表名不能为空');
        return;
    }
    
    try {
        const response = await fetch('/api/table', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ table_name: tableName })
        });
        
        const result = await response.json();
        
        if (result.success) {
            currentTable = tableName;
            document.getElementById('current-table').textContent = tableName;
            updateConfigTableNames();
            showNotification('表已切换', 'success');
        } else {
            showNotification('错误: ' + result.error, 'error');
        }
    } catch (error) {
        alert('请求失败: ' + error.message);
    }
}

// 显示配置模态框
async function showConfigModal() {
    await loadConfig();
    updateConfigTableNames();  // 确保表名是最新的
    const modal = new bootstrap.Modal(document.getElementById('configModal'));
    modal.show();
}

// 加载配置
async function loadConfig() {
    try {
        const response = await fetch('/api/config');
        const result = await response.json();
        
        if (result.success) {
            const config = result.data;
            const traffic = config.traffic_db || {};
            const sales = config.sales_db || {};
            const pallet = config.pallet_db || {};
            const product = config.product_db || {};
            const table = config.current_table || currentTable;

            document.getElementById('traffic-host').value = traffic.host || '';
            document.getElementById('traffic-port').value = traffic.port || '';
            document.getElementById('traffic-database').value = traffic.database || '';
            document.getElementById('traffic-user').value = traffic.user || '';
            document.getElementById('traffic-password').value = traffic.password || '';

            document.getElementById('sales-host').value = sales.host || '';
            document.getElementById('sales-port').value = sales.port || '';
            document.getElementById('sales-database').value = sales.database || '';
            document.getElementById('sales-user').value = sales.user || '';
            document.getElementById('sales-password').value = sales.password || '';

            document.getElementById('pallet-host').value = pallet.host || '';
            document.getElementById('pallet-port').value = pallet.port || '';
            document.getElementById('pallet-database').value = pallet.database || '';
            document.getElementById('pallet-user').value = pallet.user || '';
            document.getElementById('pallet-password').value = pallet.password || '';

            document.getElementById('product-host').value = product.host || '';
            document.getElementById('product-port').value = product.port || '';
            document.getElementById('product-database').value = product.database || '';
            document.getElementById('product-user').value = product.user || '';
            document.getElementById('product-password').value = product.password || '';
            
            updateConfigTableNames();
        }
    } catch (error) {
        console.error('加载配置失败:', error);
    }
}

// 更新配置中的表名
function updateConfigTableNames() {
    const tableName = document.getElementById('current-table').textContent;
    document.getElementById('traffic-table').value = tableName;
    document.getElementById('sales-table').value = tableName + '_Sales';
}

// 保存配置
async function saveConfig() {
    const trafficDb = {
        host: document.getElementById('traffic-host').value,
        port: parseInt(document.getElementById('traffic-port').value),
        database: document.getElementById('traffic-database').value,
        user: document.getElementById('traffic-user').value,
        password: document.getElementById('traffic-password').value,
        charset: 'utf8mb4'
    };

    const salesDb = {
        host: document.getElementById('sales-host').value,
        port: parseInt(document.getElementById('sales-port').value),
        database: document.getElementById('sales-database').value,
        user: document.getElementById('sales-user').value,
        password: document.getElementById('sales-password').value,
        charset: 'utf8mb4'
    };

    const palletDb = {
        host: document.getElementById('pallet-host').value,
        port: parseInt(document.getElementById('pallet-port').value) || 3306,
        database: document.getElementById('pallet-database').value,
        user: document.getElementById('pallet-user').value,
        password: document.getElementById('pallet-password').value,
        charset: 'utf8mb4'
    };

    const productDb = {
        host: document.getElementById('product-host').value,
        port: parseInt(document.getElementById('product-port').value) || 3306,
        database: document.getElementById('product-database').value,
        user: document.getElementById('product-user').value,
        password: document.getElementById('product-password').value,
        charset: 'utf8mb4'
    };
    
    try {
        const response = await fetch('/api/config', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                traffic_db: trafficDb,
                sales_db: salesDb,
                pallet_db: palletDb,
                product_db: productDb
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            showNotification('配置已保存', 'success');
            bootstrap.Modal.getInstance(document.getElementById('configModal')).hide();
        } else {
            showNotification('保存失败: ' + result.error, 'error');
        }
    } catch (error) {
        showNotification('请求失败: ' + error.message, 'error');
    }
}

// 功能1：快速查找
function showFunction1() {
    // 隐藏功能6和功能7面板，显示功能内容区域
    const function6Content = document.getElementById('function6-content');
    if (function6Content) {
        function6Content.style.display = 'none';
    }
    const function7Content = document.getElementById('function7-content');
    if (function7Content) {
        function7Content.style.display = 'none';
    }
    const functionContent = document.getElementById('function-content');
    if (functionContent) {
        functionContent.style.display = 'block';
    }
    
    const content = `
        <h4>快速查找</h4>
        <div class="mb-3">
            <label for="goods-id-input" class="form-label">Goods ID:</label>
            <div class="input-group">
                <input type="text" class="form-control" id="goods-id-input" placeholder="请输入goods_id（支持按Enter键查找）" onkeydown="if(event.key === 'Enter') { event.preventDefault(); doQuickSearch(); }" onblur="this.value = this.value.trim();">
                <button class="btn btn-primary" onclick="doQuickSearch()">查找</button>
            </div>
        </div>
        <div id="function1-result"></div>
    `;
    document.getElementById('function-content').innerHTML = content;
}

async function doQuickSearch() {
    const goodsId = document.getElementById('goods-id-input').value.trim();
    
    if (!goodsId) {
        alert('请输入goods_id');
        return;
    }
    
    const resultDiv = document.getElementById('function1-result');
    resultDiv.innerHTML = '<p>正在查询...</p>';
    
    try {
        const response = await fetch('/api/function1/quick_search', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ goods_id: goodsId })
        });
        
        const result = await response.json();
        
        if (result.success) {
            const data = result.data;
            let html = '<h5>查询结果</h5>';
            
            // 将两幅图放在同一行
            if (data.trend_image || data.scatter_image) {
                html += '<div style="display: flex; gap: 20px; align-items: flex-start; flex-wrap: wrap; margin: 20px 0;">';
                
                // 双轴图
                if (data.trend_image) {
                    html += '<div class="image-container" style="flex: 1; min-width: 400px;"><h6>曝光与动销趋势图</h6>';
                    html += `<img src="data:image/png;base64,${data.trend_image}" alt="趋势图">`;
                    html += '</div>';
                }
                
                // 散点图
                if (data.scatter_image) {
                    html += '<div class="image-container" style="flex: 1; min-width: 400px;"><h6>曝光与点击散点图</h6>';
                    html += `<img src="data:image/png;base64,${data.scatter_image}" alt="散点图">`;
                    html += '</div>';
                }
                
                html += '</div>';
            }
            
            // 数据摘要
            if (data.summary) {
                html += '<div class="summary-box"><h6>数据摘要</h6>';
                html += `<p>日期范围: ${data.summary.date_range}</p>`;
                html += `<p>总曝光量: ${data.summary.total_impressions}</p>`;
                html += `<p>平均曝光量: ${data.summary.avg_impressions}</p>`;
                html += `<p>最大曝光量: ${data.summary.max_impressions}</p>`;
                html += `<p>总动销人数: ${data.summary.total_buyers}</p>`;
                html += `<p>有动销的天数: ${data.summary.days_with_buyers}</p>`;
                html += `<p>相关系数: ${data.summary.correlation}</p>`;
                html += '</div>';
            }
            
            resultDiv.innerHTML = html;
        } else {
            resultDiv.innerHTML = `<div class="error-message">错误: ${result.error}</div>`;
        }
    } catch (error) {
        resultDiv.innerHTML = `<div class="error-message">请求失败: ${error.message}</div>`;
    }
}

// 功能2：动销品管理
function showFunction2() {
    // 隐藏功能6和功能7面板，显示功能内容区域
    const function6Content = document.getElementById('function6-content');
    if (function6Content) {
        function6Content.style.display = 'none';
    }
    const function7Content = document.getElementById('function7-content');
    if (function7Content) {
        function7Content.style.display = 'none';
    }
    const functionContent = document.getElementById('function-content');
    if (functionContent) {
        functionContent.style.display = 'block';
    }
    
    // 设置默认日期为昨天
    const yesterday = new Date();
    yesterday.setDate(yesterday.getDate() - 1);
    const yesterdayStr = yesterday.toISOString().split('T')[0];
    
    const content = `
        <h4>动销品管理</h4>
        <div class="mb-3">
            <label for="target-date-input" class="form-label">目标日期 (默认昨天，可修改):</label>
            <div class="input-group">
                <input type="date" class="form-control" id="target-date-input" value="${yesterdayStr}">
                <button class="btn btn-primary" onclick="doDynamicManagement()">分析</button>
                <button class="btn btn-warning" onclick="refreshStatusData()">刷新数据</button>
                <button class="btn btn-info" onclick="quickRefreshStatusData()">快速刷新</button>
                <button class="btn btn-secondary" onclick="clearFunction2Cache()">清除缓存</button>
                <button class="btn btn-success" onclick="showExportFunction2Modal()">导出数据</button>
            </div>
        </div>
        <div class="mb-3">
            <div class="mb-2">
                <label class="form-label" style="font-weight: bold; color: #0d6efd;">图片渲染模式：</label>
                <div style="margin-left: 20px; padding: 10px; background: #f0f8ff; border-left: 4px solid #4a90e2; border-radius: 4px;">
                    <div style="display: flex; flex-wrap: wrap; gap: 4px 12px;">
                        <div class="form-check" style="margin-bottom: 0;">
                            <input class="form-check-input half-image-option" type="checkbox" value="rising" id="half-image-rising">
                            <label class="form-check-label" for="half-image-rising" style="font-size: 14px; margin-left: 4px;">
                                上升期
                            </label>
                        </div>
                        <div class="form-check" style="margin-bottom: 0;">
                            <input class="form-check-input half-image-option" type="checkbox" value="declined" id="half-image-declined">
                            <label class="form-check-label" for="half-image-declined" style="font-size: 14px; margin-left: 4px;">
                                非上升期
                            </label>
                        </div>
                        <div class="form-check" style="margin-bottom: 0;">
                            <input class="form-check-input half-image-option" type="checkbox" value="new_rising" id="half-image-new-rising">
                            <label class="form-check-label" for="half-image-new-rising" style="font-size: 14px; margin-left: 4px;">
                                新增上升期
                            </label>
                        </div>
                        <div class="form-check" style="margin-bottom: 0;">
                            <input class="form-check-input half-image-option" type="checkbox" value="new_declined" id="half-image-new-declined">
                            <label class="form-check-label" for="half-image-new-declined" style="font-size: 14px; margin-left: 4px;">
                                新增非上升期
                            </label>
                        </div>
                        <div class="form-check" style="margin-bottom: 0;">
                            <input class="form-check-input half-image-option" type="checkbox" value="updated_to_rising" id="half-image-updated-to-rising">
                            <label class="form-check-label" for="half-image-updated-to-rising" style="font-size: 14px; margin-left: 4px;">
                                更新为上升期
                            </label>
                        </div>
                        <div class="form-check" style="margin-bottom: 0;">
                            <input class="form-check-input half-image-option" type="checkbox" value="back_to_rising" id="half-image-back-to-rising">
                            <label class="form-check-label" for="half-image-back-to-rising" style="font-size: 14px; margin-left: 4px;">
                                由非上升期重回上升期
                            </label>
                        </div>
                        <div class="form-check" style="margin-bottom: 0;">
                            <input class="form-check-input half-image-option" type="checkbox" value="declined_from_rising" id="half-image-declined-from-rising">
                            <label class="form-check-label" for="half-image-declined-from-rising" style="font-size: 14px; margin-left: 4px;">
                                由上升期到非上升期
                            </label>
                        </div>
                    </div>
                </div>
                <small class="form-text text-muted" style="margin-left: 20px; margin-top: 5px; display: block; font-size: 12px; color: #6c757d;">
                    💡 所有模块都会显示数据，只有勾选的模块才会生成图片
                </small>
            </div>
            <div class="mb-2">
                <label class="form-label" style="font-weight: bold; color: #0d6efd;">过滤模式：</label>
                <div style="margin-left: 20px; padding: 12px; background: #fff5f5; border-left: 4px solid #e24a4a; border-radius: 4px;">
                    <div class="form-check mb-2">
                        <input class="form-check-input" type="checkbox" id="filter-mode-checkbox">
                        <label class="form-check-label" for="filter-mode-checkbox" style="font-size: 14px; font-weight: 500;">
                            启用过滤
                        </label>
                    </div>
                    <div id="filter-mode-inputs" style="display: none; margin-left: 20px;">
                        <div class="mb-2">
                            <label class="form-label" for="filter-mode-min">下限（最小值）：</label>
                            <input type="number" class="form-control form-control-sm" id="filter-mode-min" value="1" min="0" style="width: 100px; display: inline-block;">
                            <small class="form-text text-muted">（所有历史日期的Buyers总和 >= 此值）</small>
                        </div>
                        <div class="mb-2">
                            <label class="form-label" for="filter-mode-max">上限（最大值）：</label>
                            <input type="number" class="form-control form-control-sm" id="filter-mode-max" value="" min="0" style="width: 100px; display: inline-block;" placeholder="不限制">
                            <small class="form-text text-muted">（所有历史日期的Buyers总和 <= 此值，留空表示不限制）</small>
                        </div>
                    </div>
                </div>
            </div>
            <div class="form-check">
                <input class="form-check-input" type="checkbox" id="no-cache-checkbox">
                <label class="form-check-label" for="no-cache-checkbox">
                    非缓存模式
                </label>
            </div>
        </div>
        <div id="function2-result"></div>
        
        <!-- 功能说明（折叠） -->
        <div style="margin-top: 30px; padding: 10px; background: #e7f3ff; border-left: 4px solid #0d6efd; border-radius: 4px;">
            <h6 style="margin-top: 0; color: #084298; cursor: pointer;" onclick="toggleFunction2Help('function2-help-content')">
                📖 功能说明：<span style="font-size: 12px; margin-left: 10px;">(点击展开/折叠)</span>
            </h6>
            <div id="function2-help-content" style="display: none; margin-top: 10px; color: #084298;">
                <div style="line-height: 1.8;">
                    <h6 style="color: #084298; margin-top: 15px; margin-bottom: 10px;">一、核心概念定义</h6>
                    <p><strong>动销品定义：</strong></p>
                    <ul style="margin-left: 20px; margin-bottom: 15px;">
                        <li>在 Vida_Sales 表中，该 goods_id 至少有一个 date_label 对应的 Buyers 不为空且大于0</li>
                        <li>只要历史上有过动销记录，就视为动销品</li>
                    </ul>
                    <p><strong>首次动销日期：</strong></p>
                    <ul style="margin-left: 20px; margin-bottom: 15px;">
                        <li>某个 goods_id 在 Vida_Sales 表中，Buyers > 0 的最早日期</li>
                    </ul>
                    
                    <h6 style="color: #084298; margin-top: 15px; margin-bottom: 10px;">二、按钮功能说明</h6>
                    <p><strong>1. 分析按钮</strong></p>
                    <p style="margin-left: 20px; margin-bottom: 10px;"><strong>功能：</strong>分析选定日期的动销品状态</p>
                    <p style="margin-left: 20px; margin-bottom: 10px;"><strong>逻辑：</strong></p>
                    <ul style="margin-left: 40px; margin-bottom: 15px;">
                        <li>默认使用昨天日期，可手动修改</li>
                        <li>受"图片渲染模式"和"非缓存模式"影响</li>
                        <li>未选中"非缓存模式"时，优先使用缓存（如有）</li>
                        <li>选中"非缓存模式"时，忽略缓存，重新分析并覆盖缓存</li>
                        <li>检查选定日期和前一天是否有数据，如无则提示刷新</li>
                        <li>自动更新缺失的 Status 数据</li>
                        <li>统计上升期/非上升期数量，并分类变更类型</li>
                        <li>所有模块都会显示数据，根据"图片渲染模式"选择决定生成哪些图片</li>
                    </ul>
                    
                    <p><strong>2. 刷新数据按钮</strong></p>
                    <p style="margin-left: 20px; margin-bottom: 10px;"><strong>功能：</strong>完整刷新所有动销品的 Status 数据</p>
                    <p style="margin-left: 20px; margin-bottom: 10px;"><strong>逻辑：</strong></p>
                    <ul style="margin-left: 40px; margin-bottom: 15px;">
                        <li>获取所有动销品 goods_id</li>
                        <li>对每个动销品：找到首次动销日期；清除首次动销日期之前的所有 Status 数据（设为 NULL）；从首次动销日期到昨天，逐日计算并更新 Status</li>
                        <li>检查昨天及之前缺失数据的日期范围</li>
                        <li>报告缺失数据信息（可折叠显示）</li>
                    </ul>
                    
                    <p><strong>3. 快速刷新（仅昨天）按钮</strong></p>
                    <p style="margin-left: 20px; margin-bottom: 10px;"><strong>功能：</strong>仅刷新所有动销品在昨天的 Status 数据</p>
                    <p style="margin-left: 20px; margin-bottom: 10px;"><strong>逻辑：</strong></p>
                    <ul style="margin-left: 40px; margin-bottom: 15px;">
                        <li>获取所有动销品 goods_id（不限于昨天有动销的）</li>
                        <li>对每个动销品，检查昨天是否有 Traffic 数据</li>
                        <li>如有 Traffic 数据，计算并更新 Status</li>
                        <li>如无 Traffic 数据，跳过（可能是正常下架）</li>
                    </ul>
                    
                    <p><strong>4. 清除缓存按钮</strong></p>
                    <p style="margin-left: 20px; margin-bottom: 10px;"><strong>功能：</strong>清除前端 sessionStorage 中的缓存数据</p>
                    <p style="margin-left: 20px; margin-bottom: 10px;"><strong>逻辑：</strong>删除 function2_cache 键，下次分析将重新计算</p>
                    
                    <p><strong>5. 导出数据按钮</strong></p>
                    <p style="margin-left: 20px; margin-bottom: 10px;"><strong>功能：</strong>导出动销品管理数据</p>
                    <p style="margin-left: 20px; margin-bottom: 10px;"><strong>逻辑：</strong></p>
                    <ul style="margin-left: 40px; margin-bottom: 15px;">
                        <li>可选择导出格式（Excel/CSV）</li>
                        <li>可选择状态筛选（上升期/非上升期/全部/由上升期到非上升期）</li>
                        <li>可选择日期范围（单日/全历史）</li>
                        <li>可选择导出字段</li>
                    </ul>
                    
                    <h6 style="color: #084298; margin-top: 15px; margin-bottom: 10px;">三、分类准则说明</h6>
                    <p><strong>1. 上升期（Status=1）</strong></p>
                    <p style="margin-left: 20px; margin-bottom: 10px;"><strong>定义：</strong>选定日期有 Status=1 的商品</p>
                    <p style="margin-left: 20px; margin-bottom: 10px;"><strong>判断方法：</strong>基于曝光量趋势分析</p>
                    <ul style="margin-left: 40px; margin-bottom: 15px;">
                        <li>使用线性回归分析近期趋势</li>
                        <li>如果趋势上升或未明显下降，判定为上升期</li>
                    </ul>
                    
                    <p><strong>2. 非上升期（Status=2）</strong></p>
                    <p style="margin-left: 20px; margin-bottom: 10px;"><strong>定义：</strong>包括两类商品</p>
                    <ul style="margin-left: 40px; margin-bottom: 10px;">
                        <li>选定日期有 Status=2 的商品</li>
                        <li>下架缺货的商品（选定日期没有数据，但之前有动销记录）</li>
                    </ul>
                    <p style="margin-left: 20px; margin-bottom: 10px;"><strong>判断方法：</strong></p>
                    <ul style="margin-left: 40px; margin-bottom: 15px;">
                        <li>Status=2：曝光量趋势下降或已过峰值</li>
                        <li>下架缺货：在选定日期没有 Traffic 数据，但之前有数据</li>
                    </ul>
                    
                    <p><strong>3. 新增上升期</strong></p>
                    <p style="margin-left: 20px; margin-bottom: 10px;"><strong>条件：</strong></p>
                    <ul style="margin-left: 40px; margin-bottom: 15px;">
                        <li>选定日期 Status=1（上升期）</li>
                        <li>前一天没有 Status 数据</li>
                        <li>历史（选定日期之前）没有 Status 数据</li>
                    </ul>
                    <p style="margin-left: 20px; margin-bottom: 10px;"><strong>说明：</strong>首次出现且为上升期的商品</p>
                    
                    <p><strong>4. 新增非上升期</strong></p>
                    <p style="margin-left: 20px; margin-bottom: 10px;"><strong>条件：</strong></p>
                    <ul style="margin-left: 40px; margin-bottom: 15px;">
                        <li>选定日期 Status=2</li>
                        <li>前一天没有 Status 数据</li>
                        <li>选定日期前一直没有数据（该商品首次出现）</li>
                    </ul>
                    
                    <p><strong>5. 更新为上升期</strong></p>
                    <p style="margin-left: 20px; margin-bottom: 10px;"><strong>条件：</strong></p>
                    <ul style="margin-left: 40px; margin-bottom: 15px;">
                        <li>选定日期 Status=1</li>
                        <li>前一天没有 Status 数据，但历史有 Status 数据（可能是缺货后恢复）</li>
                        <li>最近历史状态为1，但前一天没有数据（之前是上升期，中间缺货后恢复）</li>
                        <li>或：没有找到最近历史状态，但之前有数据</li>
                    </ul>
                    <p style="margin-left: 20px; margin-bottom: 10px;"><strong>说明：</strong>之前是上升期，中间可能缺货，现在恢复为上升期</p>
                    
                    <p><strong>6. 由非上升期重回上升期</strong></p>
                    <p style="margin-left: 20px; margin-bottom: 10px;"><strong>条件（满足其一）：</strong></p>
                    <ul style="margin-left: 40px; margin-bottom: 15px;">
                        <li>前一天 Status=2，选定日期 Status=1</li>
                        <li>前一天没有 Status 数据，但历史最近一次 Status=2</li>
                    </ul>
                    <p style="margin-left: 20px; margin-bottom: 10px;"><strong>说明：</strong>从非上升期恢复到上升期（简化判断，不检查上升趋势）</p>
                    
                    <p><strong>7. 由上升期到非上升期</strong></p>
                    <p style="margin-left: 20px; margin-bottom: 10px;"><strong>条件：</strong></p>
                    <ul style="margin-left: 40px; margin-bottom: 10px;">
                        <li>选定日期 Status=2</li>
                        <li>前一天 Status=1</li>
                    </ul>
                    <p style="margin-left: 20px; margin-bottom: 10px;"><strong>说明：</strong>这是需要重点关注的变更类型，会特别标记（!!!）</p>
                    
                    <h6 style="color: #084298; margin-top: 15px; margin-bottom: 10px;">四、特殊说明</h6>
                    <p><strong>1. 缺货/下架处理</strong></p>
                    <ul style="margin-left: 40px; margin-bottom: 15px;">
                        <li>如果某个商品前一天没有 Status 数据，但其他商品都有数据，判定为缺货/下架</li>
                        <li>缺货/下架的商品会被标记为 Status=2（非上升期）</li>
                        <li>在非上升期图表中显示，数据截止到最后一个有数据的日期</li>
                    </ul>
                    
                    <p><strong>2. 数据缺失处理</strong></p>
                    <ul style="margin-left: 40px; margin-bottom: 15px;">
                        <li>如果所有商品前一天都没有数据，系统会尝试向前查找并导入缺失数据</li>
                        <li>如果数据库确实缺少数据，会报告缺失日期范围</li>
                        <li>缺失数据信息会以可折叠方式显示</li>
                    </ul>
                    
                    <p><strong>3. 缓存机制</strong></p>
                    <ul style="margin-left: 40px; margin-bottom: 15px;">
                        <li>缓存保存在 Cache_Dynamic 目录，格式为 JSON</li>
                        <li>缓存不包含图片数据（base64 图片太大）</li>
                        <li>非缓存模式会重新分析并覆盖原有缓存</li>
                    </ul>
                    
                    <p><strong>4. 统计数量计算</strong></p>
                    <ul style="margin-left: 40px; margin-bottom: 15px;">
                        <li><strong>计算上升期</strong> = 前一天上升期数量 + 新增上升期 + 更新为上升期 + 由非上升期重回上升期 - 由上升期到非上升期</li>
                        <li><strong>实际上升期</strong> = 选定日期有 Status=1 的商品数量</li>
                        <li>非上升期数量 = 选定日期有 Status=2 的商品数量 + 下架缺货的商品数量</li>
                        <li>总数 = 实际上升期数量 + 非上升期数量 = 所有动销品数量</li>
                    </ul>
                    <p style="margin-left: 20px; margin-bottom: 10px;"><strong>说明：</strong></p>
                    <ul style="margin-left: 40px; margin-bottom: 15px;">
                        <li>前一天上升期：是指前一天的实际上升期</li>
                        <li>计算上升期：根据前一天上升期数量和各类变更数量计算得出的理论上升期数量</li>
                        <li>实际上升期：选定日期Status=1的数量（数据库实际状态）</li>
                        <li>通过对比计算上升期和实际上升期，可以验证数据一致性</li>
                    </ul>
                    
                    <h6 style="color: #084298; margin-top: 15px; margin-bottom: 10px;">五、选项说明</h6>
                    <p><strong>1. 图片渲染模式（多选）</strong></p>
                    <p style="margin-left: 20px; margin-bottom: 10px;">可以选择性地生成特定类别的图片，勾选哪部分就渲染哪部分的图片。所有模块都会显示数据（文字信息），只有勾选的模块才会生成图片。</p>
                    <p style="margin-left: 20px; margin-bottom: 10px;">可选类别（共7个）：</p>
                    <ul style="margin-left: 40px; margin-bottom: 15px;">
                        <li><strong>上升期</strong>：所有上升期商品的图片</li>
                        <li><strong>非上升期</strong>：所有非上升期商品的图片</li>
                        <li><strong>新增上升期</strong>：新增上升期商品的图片</li>
                        <li><strong>新增非上升期</strong>：新增非上升期商品的图片</li>
                        <li><strong>更新为上升期</strong>：更新为上升期商品的图片</li>
                        <li><strong>由非上升期重回上升期</strong>：由非上升期重回上升期商品的图片</li>
                        <li><strong>由上升期到非上升期</strong>：由上升期到非上升期商品的图片（重点关注）</li>
                    </ul>
                    <p style="margin-left: 20px; margin-bottom: 10px;"><strong>显示格式：</strong>每个模块的标题前会显示 ▶ 图标，标题以加粗形式显示，例如：<strong>▶ 新增上升期：2个</strong></p>
                    
                    <p><strong>2. 过滤模式</strong></p>
                    <p style="margin-left: 20px; margin-bottom: 10px;">可以设置下限和上限来过滤商品：</p>
                    <ul style="margin-left: 40px; margin-bottom: 15px;">
                        <li><strong>不过滤</strong>：显示所有动销品（Buyers > 0）</li>
                        <li><strong>启用过滤</strong>：可以设置下限（最小值）和上限（最大值）</li>
                        <li><strong>下限</strong>：所有历史日期的Buyers总和 >= 此值的商品</li>
                        <li><strong>上限</strong>：所有历史日期的Buyers总和 <= 此值的商品（留空表示不限制上限）</li>
                        <li><strong>示例</strong>：下限=1，上限=10，表示只显示Buyers总和在1到10之间的商品</li>
                    </ul>
                    
                    <p><strong>3. 非缓存模式</strong></p>
                    <p style="margin-left: 20px; margin-bottom: 10px;">选中后重新分析，不使用缓存数据，并覆盖原有缓存</p>
                </div>
            </div>
        </div>
        
        <!-- 导出选项模态框 -->
        <div class="modal fade" id="exportFunction2Modal" tabindex="-1">
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">导出选项</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <div class="mb-3">
                            <label class="form-label">导出格式:</label>
                            <select class="form-select" id="export-format-select">
                                <option value="xlsx">Excel (.xlsx)</option>
                                <option value="csv">CSV (.csv)</option>
                            </select>
                        </div>
                        <div class="mb-3">
                            <label class="form-label">状态筛选:</label>
                            <select class="form-select" id="status-filter-select">
                                <option value="all">全部 (上升期 + 非上升期)</option>
                                <option value="1">上升期 (Status=1)</option>
                                <option value="2">非上升期 (Status=2)</option>
                                <option value="declined_from_rising">由上升期到非上升期</option>
                            </select>
                        </div>
                        <div class="mb-3">
                            <label class="form-label">日期范围:</label>
                            <select class="form-select" id="date-range-select">
                                <option value="single">只导出选择日期的数据</option>
                                <option value="all">导出每个goods_id的所有历史日期</option>
                            </select>
                        </div>
                        <div class="mb-3">
                            <label class="form-label">选择导出字段:</label>
                            <div style="max-height: 200px; overflow-y: auto; border: 1px solid #ddd; padding: 10px; border-radius: 4px;">
                                <div class="mb-2">
                                    <button type="button" class="btn btn-sm btn-outline-primary" onclick="selectAllFields()">全选</button>
                                    <button type="button" class="btn btn-sm btn-outline-secondary" onclick="deselectAllFields()">全不选</button>
                                </div>
                                <div id="field-selection-container">
                                    <div class="form-check">
                                        <input class="form-check-input field-checkbox" type="checkbox" value="goods_id" id="field-goods_id" checked>
                                        <label class="form-check-label" for="field-goods_id">goods_id</label>
                                    </div>
                                    <div class="form-check">
                                        <input class="form-check-input field-checkbox" type="checkbox" value="date_label" id="field-date_label" checked>
                                        <label class="form-check-label" for="field-date_label">date_label</label>
                                    </div>
                                    <div class="form-check">
                                        <input class="form-check-input field-checkbox" type="checkbox" value="Product impressions" id="field-impressions" checked>
                                        <label class="form-check-label" for="field-impressions">Product impressions</label>
                                    </div>
                                    <div class="form-check">
                                        <input class="form-check-input field-checkbox" type="checkbox" value="Number of visitor impressions of the product" id="field-visitor-impressions">
                                        <label class="form-check-label" for="field-visitor-impressions">Number of visitor impressions of the product</label>
                                    </div>
                                    <div class="form-check">
                                        <input class="form-check-input field-checkbox" type="checkbox" value="Product clicks" id="field-clicks" checked>
                                        <label class="form-check-label" for="field-clicks">Product clicks</label>
                                    </div>
                                    <div class="form-check">
                                        <input class="form-check-input field-checkbox" type="checkbox" value="Number of visitor clicks on the product" id="field-visitor-clicks">
                                        <label class="form-check-label" for="field-visitor-clicks">Number of visitor clicks on the product</label>
                                    </div>
                                    <div class="form-check">
                                        <input class="form-check-input field-checkbox" type="checkbox" value="CTR" id="field-ctr" checked>
                                        <label class="form-check-label" for="field-ctr">CTR</label>
                                    </div>
                                    <div class="form-check">
                                        <input class="form-check-input field-checkbox" type="checkbox" value="Status" id="field-status" checked>
                                        <label class="form-check-label" for="field-status">Status</label>
                                    </div>
                                    <div class="form-check">
                                        <input class="form-check-input field-checkbox" type="checkbox" value="Reason" id="field-reason">
                                        <label class="form-check-label" for="field-reason">Reason</label>
                                    </div>
                                    <div class="form-check">
                                        <input class="form-check-input field-checkbox" type="checkbox" value="Video" id="field-video">
                                        <label class="form-check-label" for="field-video">Video</label>
                                    </div>
                                    <div class="form-check">
                                        <input class="form-check-input field-checkbox" type="checkbox" value="Price" id="field-price">
                                        <label class="form-check-label" for="field-price">Price</label>
                                    </div>
                                    <div class="form-check">
                                        <input class="form-check-input field-checkbox" type="checkbox" value="Buyers" id="field-buyers" checked>
                                        <label class="form-check-label" for="field-buyers">Buyers</label>
                                    </div>
                                </div>
                            </div>
                            <small class="form-text text-muted">至少选择一个字段，如果全不选则导出所有字段</small>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">取消</button>
                        <button type="button" class="btn btn-primary" onclick="exportFunction2Data()">导出</button>
                    </div>
                </div>
            </div>
        </div>
    `;
    document.getElementById('function-content').innerHTML = content;
    
    // 检查是否有缓存（只显示文本信息，不显示图片）
    const cachedData = sessionStorage.getItem('function2_cache');
    if (cachedData) {
        try {
            const data = JSON.parse(cachedData);
            // 显示缓存的结果（不包含图片，只显示统计信息和商品信息）
            displayFunction2ResultFromCache(data);
        } catch (e) {
            console.error('加载缓存失败:', e);
        }
    }
    
    // 添加过滤模式复选框的事件监听器
    const filterModeCheckbox = document.getElementById('filter-mode-checkbox');
    const filterModeInputs = document.getElementById('filter-mode-inputs');
    if (filterModeCheckbox && filterModeInputs) {
        filterModeCheckbox.addEventListener('change', function() {
            filterModeInputs.style.display = this.checked ? 'block' : 'none';
        });
    }
}

async function refreshStatusData() {
    const resultDiv = document.getElementById('function2-result');
    resultDiv.innerHTML = '<div class="alert alert-info">正在刷新数据，请稍候...</div>';
    
    try {
        const response = await fetch('/api/function2/refresh_status', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        const result = await response.json();
        
        if (result.success) {
            let message = `<div class="alert alert-success">${result.message}</div>`;
            if (result.missing_dates_info && result.missing_dates_info.length > 0) {
                message += `<div class="alert alert-warning">${result.missing_dates_info[0].message}</div>`;
            }
            resultDiv.innerHTML = message;
        } else {
            resultDiv.innerHTML = `<div class="alert alert-danger">刷新失败: ${result.message || '未知错误'}</div>`;
        }
    } catch (error) {
        resultDiv.innerHTML = `<div class="alert alert-danger">请求失败: ${error.message}</div>`;
    }
}

async function quickRefreshStatusData() {
    const resultDiv = document.getElementById('function2-result');
    
    // 获取用户选择的日期
    let targetDate = document.getElementById('target-date-input').value;
    // 如果没有输入日期，使用昨天
    if (!targetDate) {
        const yesterday = new Date();
        yesterday.setDate(yesterday.getDate() - 1);
        targetDate = yesterday.toISOString().split('T')[0];
    }
    
    resultDiv.innerHTML = `<div class="alert alert-info">正在快速刷新 ${targetDate} 的数据，请稍候...</div>`;
    
    try {
        const response = await fetch('/api/function2/quick_refresh_status', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                target_date: targetDate
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            let message = `<div class="alert alert-success">${result.message}</div>`;
            if (result.missing_dates_info && result.missing_dates_info.length > 0) {
                message += `<div class="alert alert-warning">${result.missing_dates_info[0].message}</div>`;
            }
            resultDiv.innerHTML = message;
        } else {
            resultDiv.innerHTML = `<div class="alert alert-danger">快速刷新失败: ${result.message || '未知错误'}</div>`;
        }
    } catch (error) {
        resultDiv.innerHTML = `<div class="alert alert-danger">请求失败: ${error.message}</div>`;
    }
}

async function doDynamicManagement() {
    let targetDate = document.getElementById('target-date-input').value;
    // 如果没有输入日期，使用昨天
    if (!targetDate) {
        const yesterday = new Date();
        yesterday.setDate(yesterday.getDate() - 1);
        targetDate = yesterday.toISOString().split('T')[0];
    }
    
    // 获取图片渲染模式选项（多选）
    const halfImageOptions = document.querySelectorAll('.half-image-option:checked');
    let halfImageMode = [];  // 默认值：空列表，不生成任何图片
    if (halfImageOptions.length > 0) {
        // 如果选择了任何选项，将选中的值作为列表发送
        halfImageMode = Array.from(halfImageOptions).map(option => option.value);
    }
    // 获取过滤模式选项
    const filterModeEnabled = document.getElementById('filter-mode-checkbox').checked;
    let filterMode = null;
    if (filterModeEnabled) {
        const minValue = document.getElementById('filter-mode-min').value;
        const maxValue = document.getElementById('filter-mode-max').value;
        filterMode = {
            'min': minValue ? parseInt(minValue) : 0,
            'max': maxValue ? parseInt(maxValue) : null
        };
    }
    // 获取非缓存模式选项
    const noCache = document.getElementById('no-cache-checkbox').checked;
    const useCache = !noCache;  // 非缓存模式时，use_cache为false
    
    const resultDiv = document.getElementById('function2-result');
    resultDiv.innerHTML = '<p>正在分析...</p>';
    
    try {
        const response = await fetch('/api/function2/dynamic_management', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ 
                target_date: targetDate,
                use_cache: useCache,
                half_image_mode: halfImageMode,
                filter_mode: filterMode
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            // 保存到缓存（不包含图片数据，因为图片太大）
            const cacheData = {
                statistics: result.data.statistics,
                rising: {
                    goods_info: result.data.rising.goods_info,
                    summary: result.data.rising.summary
                },
                declined: {
                    goods_info: result.data.declined.goods_info,
                    summary: result.data.declined.summary
                },
                // 不缓存images，因为base64图片数据太大
                has_images: {
                    rising: result.data.rising.images && result.data.rising.images.length > 0,
                    declined: result.data.declined.images && result.data.declined.images.length > 0
                }
            };
            
            try {
                sessionStorage.setItem('function2_cache', JSON.stringify(cacheData));
            } catch (e) {
                // 如果存储失败（配额超限），清除旧缓存后重试
                console.warn('存储缓存失败，尝试清除旧缓存:', e);
                try {
                    sessionStorage.removeItem('function2_cache');
                    sessionStorage.setItem('function2_cache', JSON.stringify(cacheData));
                } catch (e2) {
                    console.error('无法保存缓存:', e2);
                }
            }
            
            // 显示结果（使用完整数据，包含图片）
            displayFunction2Result(result.data, result.analysis_time, result.from_cache);
        } else {
            let errorHtml = `<div class="error-message">错误: ${result.error}</div>`;
            if (result.analysis_time !== undefined && result.analysis_time !== null) {
                errorHtml = `<div class="alert alert-info" style="margin-bottom: 15px;">分析耗时: ${result.analysis_time} 秒</div>` + errorHtml;
            }
            resultDiv.innerHTML = errorHtml;
        }
    } catch (error) {
        resultDiv.innerHTML = `<div class="error-message">请求失败: ${error.message}</div>`;
    }
}

// 显示功能2的结果
function displayFunction2Result(data, analysisTime, fromCache) {
    const resultDiv = document.getElementById('function2-result');
    let html = '<h5>分析结果</h5>';
    
    // 显示分析时间和缓存提示
    if (analysisTime !== undefined && analysisTime !== null) {
        let timeInfo = `分析耗时: ${analysisTime} 秒`;
        if (fromCache) {
            timeInfo += ' (来自缓存)';
        }
        html += `<div class="alert alert-info" style="margin-bottom: 15px;">${timeInfo}</div>`;
    }
    
    // 统计信息
    if (data.statistics) {
        const stats = data.statistics;
        html += '<div class="summary-box" style="background: #f8f9fa; border-left: 4px solid #0d6efd; max-width: 600px;">';
        html += '<h6 style="margin-top: 0; color: #0d6efd; font-weight: bold;">统计信息</h6>';
        html += '<table style="width: 100%; border-collapse: collapse;">';
        html += `<tr><td style="padding: 4px 8px; width: auto; white-space: nowrap;"><strong>日期：</strong></td><td style="padding: 4px 8px; text-align: right; font-weight: bold; width: 100%;">${stats.date}</td></tr>`;
        html += `<tr><td colspan="2" style="padding: 8px 8px 4px 8px; font-weight: bold; border-top: 1px solid #ddd;">上升期统计:</td></tr>`;
        html += `<tr><td style="padding: 4px 8px; padding-left: 20px; white-space: nowrap;">前一天上升期:</td><td style="padding: 4px 8px; text-align: right; font-weight: bold;">${stats.previous_rising_count || 0}个</td></tr>`;
        html += `<tr><td style="padding: 4px 8px; padding-left: 20px; white-space: nowrap;">计算上升期:</td><td style="padding: 4px 8px; text-align: right; font-weight: bold;">${stats.calculated_rising_count || stats.rising_count}个</td></tr>`;
        html += `<tr><td style="padding: 4px 8px; padding-left: 20px; white-space: nowrap;">实际上升期:</td><td style="padding: 4px 8px; text-align: right; font-weight: bold; color: #198754;">${stats.rising_count}个</td></tr>`;
        html += `<tr><td colspan="2" style="padding: 8px 8px 4px 8px; font-weight: bold; border-top: 1px solid #ddd;">非上升期统计:</td></tr>`;
        html += `<tr><td style="padding: 4px 8px; padding-left: 20px; white-space: nowrap;">非上升期:</td><td style="padding: 4px 8px; text-align: right; font-weight: bold;">${stats.declined_count}个</td></tr>`;
        html += `<tr><td colspan="2" style="padding: 8px 8px 4px 8px; font-weight: bold; border-top: 1px solid #ddd;">变更统计:</td></tr>`;
        html += `<tr><td style="padding: 4px 8px; padding-left: 20px; white-space: nowrap;">新增上升期:</td><td style="padding: 4px 8px; text-align: right; font-weight: bold;">${stats.new_rising}个</td></tr>`;
        html += `<tr><td style="padding: 4px 8px; padding-left: 20px; white-space: nowrap;">新增非上升期:</td><td style="padding: 4px 8px; text-align: right; font-weight: bold;">${stats.new_declined}个</td></tr>`;
        html += `<tr><td style="padding: 4px 8px; padding-left: 20px; white-space: nowrap;">更新为上升期:</td><td style="padding: 4px 8px; text-align: right; font-weight: bold;">${stats.updated_to_rising}个</td></tr>`;
        html += `<tr><td style="padding: 4px 8px; padding-left: 20px; white-space: nowrap;">由非上升期重回上升期:</td><td style="padding: 4px 8px; text-align: right; font-weight: bold;">${stats.back_to_rising}个</td></tr>`;
        html += `<tr><td style="padding: 4px 8px; padding-left: 20px; color: #dc3545; white-space: nowrap;"><strong>！！！由上升期到非上升期:</strong></td><td style="padding: 4px 8px; text-align: right; font-weight: bold; color: #dc3545;">${stats.declined_from_rising}个</td></tr>`;
        html += '</table>';
        
        // 显示特殊说明（可折叠）
        if (stats.special_notes && stats.special_notes.length > 0) {
            const specialNotesId = 'special-notes-' + Date.now();
            html += '<div style="margin-top: 15px; padding: 10px; background: #fff3cd; border-left: 4px solid #ffc107; border-radius: 4px;">';
            html += `<h6 style="margin-top: 0; color: #856404; cursor: pointer;" onclick="toggleSpecialNotes('${specialNotesId}')">`;
            html += '⚠️ 特殊说明：<span style="font-size: 12px; margin-left: 10px;">(点击展开/折叠)</span></h6>';
            html += `<div id="${specialNotesId}" style="display: none; margin-top: 10px;">`;
            stats.special_notes.forEach(note => {
                html += `<p style="margin: 5px 0; color: #856404;">${note}</p>`;
            });
            html += '</div>';
            html += '</div>';
        }
        
        html += '</div>';
    }
    
    // 辅助函数：显示商品信息
    function displayGoodsSection(title, goodsInfo, images, categoryName) {
        if (!goodsInfo || goodsInfo.length === 0) return '';
        
        let sectionHtml = `<h6><strong>▶ ${title}</strong></h6>`;
        
        if (images && images.length > 0) {
            const cols = 3;
            let goodsIndex = 0;
            
            images.forEach((img, imgIdx) => {
                const goodsInThisImage = Math.min(cols, goodsInfo.length - goodsIndex);
                
                sectionHtml += '<div class="goods-info-text-container" style="margin-bottom: 10px; padding: 10px; background: #f8f9fa; border-radius: 5px;">';
                for (let i = 0; i < goodsInThisImage && goodsIndex < goodsInfo.length; i++) {
                    const info = goodsInfo[goodsIndex];
                    sectionHtml += `<div style="margin: 5px 0; font-family: monospace; font-size: 14px;">${info.goods_id} - 加入时间: ${info.join_date}, Reason: ${info.reason}</div>`;
                    goodsIndex++;
                }
                sectionHtml += '</div>';
                sectionHtml += `<div class="image-container"><img src="data:image/png;base64,${img}" alt="${categoryName}图${imgIdx+1}"></div>`;
            });
        } else {
            sectionHtml += '<div class="goods-info-text-container" style="margin-bottom: 10px; padding: 10px; background: #f8f9fa; border-radius: 5px;">';
            goodsInfo.forEach(info => {
                sectionHtml += `<div style="margin: 5px 0; font-family: monospace; font-size: 14px;">${info.goods_id} - 加入时间: ${info.join_date}, Reason: ${info.reason}</div>`;
            });
            sectionHtml += '</div>';
        }
        
        return sectionHtml;
    }
    
    const stats = data.statistics || {};
    const categories = data.categories || {};
    const allCategoryGoodsIds = new Set();
    
    // 收集所有已显示的类别goods_id
    if (stats.new_rising_goods) stats.new_rising_goods.forEach(id => allCategoryGoodsIds.add(id));
    if (stats.new_declined_goods) stats.new_declined_goods.forEach(id => allCategoryGoodsIds.add(id));
    if (stats.updated_to_rising_goods) stats.updated_to_rising_goods.forEach(id => allCategoryGoodsIds.add(id));
    if (stats.back_to_rising_goods) stats.back_to_rising_goods.forEach(id => allCategoryGoodsIds.add(id));
    if (stats.declined_from_rising_goods) stats.declined_from_rising_goods.forEach(id => allCategoryGoodsIds.add(id));
    
    // 1. 新增上升期（所有模块都显示数据）
    if (stats.new_rising > 0) {
        const categoryData = categories.new_rising || {};
        const categoryGoodsInfo = categoryData.goods_info || [];
        const categoryImages = categoryData.images || [];
        html += displayGoodsSection(`新增上升期（上升期）：${stats.new_rising}个`, categoryGoodsInfo, categoryImages, '新增上升期');
    }
    
    // 2. 新增非上升期（所有模块都显示数据）
    if (stats.new_declined > 0) {
        const categoryData = categories.new_declined || {};
        const categoryGoodsInfo = categoryData.goods_info || [];
        const categoryImages = categoryData.images || [];
        html += displayGoodsSection(`新增非上升期（非上升期）：${stats.new_declined}个`, categoryGoodsInfo, categoryImages, '新增非上升期');
    }
    
    // 3. 更新为上升期（所有模块都显示数据）
    if (stats.updated_to_rising > 0) {
        const categoryData = categories.updated_to_rising || {};
        const categoryGoodsInfo = categoryData.goods_info || [];
        const categoryImages = categoryData.images || [];
        html += displayGoodsSection(`更新为上升期（上升期）：${stats.updated_to_rising}个`, categoryGoodsInfo, categoryImages, '更新为上升期');
    }
    
    // 4. 由非上升期重回上升期（所有模块都显示数据）
    if (stats.back_to_rising > 0) {
        const categoryData = categories.back_to_rising || {};
        const categoryGoodsInfo = categoryData.goods_info || [];
        const categoryImages = categoryData.images || [];
        html += displayGoodsSection(`由非上升期重回上升期（上升期）：${stats.back_to_rising}个`, categoryGoodsInfo, categoryImages, '由非上升期重回上升期');
    }
    
    // 5. 由上升期到非上升期（所有模块都显示数据）
    if (stats.declined_from_rising > 0) {
        const categoryData = categories.declined_from_rising || {};
        const categoryGoodsInfo = categoryData.goods_info || [];
        const categoryImages = categoryData.images || [];
        html += displayGoodsSection(`由上升期到非上升期（非上升期）：${stats.declined_from_rising}个`, categoryGoodsInfo, categoryImages, '由上升期到非上升期');
    }
    
    // 6. 上升期商品（剩余商品，排除已显示的类别商品）
    if (data.rising && data.rising.goods_info && data.rising.goods_info.length > 0) {
        const remainingGoodsInfo = data.rising.goods_info.filter(info => !allCategoryGoodsIds.has(info.goods_id));
        if (remainingGoodsInfo.length > 0) {
            html += `<h6><strong>▶ 历史上升期商品：${remainingGoodsInfo.length}个</strong></h6>`;
            
            if (data.rising.images && data.rising.images.length > 0) {
                const cols = 3;
                let goodsIndex = 0;
                
                data.rising.images.forEach((img, imgIdx) => {
                    const goodsInThisImage = Math.min(cols, remainingGoodsInfo.length - goodsIndex);
                    
                    html += '<div class="goods-info-text-container" style="margin-bottom: 10px; padding: 10px; background: #f8f9fa; border-radius: 5px;">';
                    for (let i = 0; i < goodsInThisImage && goodsIndex < remainingGoodsInfo.length; i++) {
                        const info = remainingGoodsInfo[goodsIndex];
                        html += `<div style="margin: 5px 0; font-family: monospace; font-size: 14px;">${info.goods_id} - 加入时间: ${info.join_date}, Reason: ${info.reason}</div>`;
                        goodsIndex++;
                    }
                    html += '</div>';
                    html += `<div class="image-container"><img src="data:image/png;base64,${img}" alt="上升期图${imgIdx+1}"></div>`;
                });
            } else {
                html += '<div class="goods-info-text-container" style="margin-bottom: 10px; padding: 10px; background: #f8f9fa; border-radius: 5px;">';
                remainingGoodsInfo.forEach(info => {
                    html += `<div style="margin: 5px 0; font-family: monospace; font-size: 14px;">${info.goods_id} - 加入时间: ${info.join_date}, Reason: ${info.reason}</div>`;
                });
                html += '</div>';
            }
        }
    }
    
    // 7. 非上升期商品（剩余商品，排除已显示的类别商品）
    if (data.declined && data.declined.goods_info && data.declined.goods_info.length > 0) {
        const remainingGoodsInfo = data.declined.goods_info.filter(info => !allCategoryGoodsIds.has(info.goods_id));
        if (remainingGoodsInfo.length > 0) {
            html += `<h6><strong>▶ 历史非上升期商品：${remainingGoodsInfo.length}个</strong></h6>`;
            
            if (data.declined.images && data.declined.images.length > 0) {
                const cols = 3;
                let goodsIndex = 0;
                
                data.declined.images.forEach((img, imgIdx) => {
                    const goodsInThisImage = Math.min(cols, remainingGoodsInfo.length - goodsIndex);
                    
                    html += '<div class="goods-info-text-container" style="margin-bottom: 10px; padding: 10px; background: #f8f9fa; border-radius: 5px;">';
                    for (let i = 0; i < goodsInThisImage && goodsIndex < remainingGoodsInfo.length; i++) {
                        const info = remainingGoodsInfo[goodsIndex];
                        html += `<div style="margin: 5px 0; font-family: monospace; font-size: 14px;">${info.goods_id} - 加入时间: ${info.join_date}, Reason: ${info.reason}</div>`;
                        goodsIndex++;
                    }
                    html += '</div>';
                    html += `<div class="image-container"><img src="data:image/png;base64,${img}" alt="非上升期图${imgIdx+1}"></div>`;
                });
            } else {
                html += '<div class="goods-info-text-container" style="margin-bottom: 10px; padding: 10px; background: #f8f9fa; border-radius: 5px;">';
                remainingGoodsInfo.forEach(info => {
                    html += `<div style="margin: 5px 0; font-family: monospace; font-size: 14px;">${info.goods_id} - 加入时间: ${info.join_date}, Reason: ${info.reason}</div>`;
                });
                html += '</div>';
            }
        }
    }
    
    // 8. 基本信息统计（统一放在最后）
    html += '<div style="margin-top: 20px;"><h6><strong>▶ 基本信息统计</strong></h6>';
    
    // 使用表格布局美化显示
    html += '<div style="display: flex; gap: 15px; flex-wrap: wrap; margin-top: 10px;">';
    
    // 上升期基本信息统计
    if (data.rising && data.rising.summary) {
        const summary = data.rising.summary;
        html += '<div class="summary-box" style="flex: 1; min-width: 300px; max-width: 500px; background: #f0f8ff; border-left: 4px solid #4a90e2;">';
        html += '<h6 style="margin-top: 0; color: #4a90e2; font-weight: bold;">上升期</h6>';
        html += '<table style="width: 100%; border-collapse: collapse;">';
        html += `<tr><td style="padding: 4px 4px 4px 8px; width: 50%;">总记录数:</td><td style="padding: 4px 8px 4px 4px; text-align: right; font-weight: bold;">${(summary.total_records || 0).toLocaleString()} 条</td></tr>`;
        html += `<tr><td style="padding: 4px 4px 4px 8px;">去重商品ID数量:</td><td style="padding: 4px 8px 4px 4px; text-align: right; font-weight: bold;">${(summary.unique_goods || 0).toLocaleString()} 个</td></tr>`;
        if (summary.min_date && summary.max_date) {
            html += `<tr><td colspan="2" style="padding: 8px 8px 4px 8px; font-weight: bold; border-top: 1px solid #ddd;">时间周期:</td></tr>`;
            html += `<tr><td style="padding: 4px 4px 4px 20px;">最早日期:</td><td style="padding: 4px 8px 4px 4px; text-align: right;">${summary.min_date}</td></tr>`;
            html += `<tr><td style="padding: 4px 4px 4px 20px;">最晚日期:</td><td style="padding: 4px 8px 4px 4px; text-align: right;">${summary.max_date}</td></tr>`;
            html += `<tr><td style="padding: 4px 4px 4px 20px;">时间跨度:</td><td style="padding: 4px 8px 4px 4px; text-align: right; font-weight: bold;">${summary.date_range} 天</td></tr>`;
        }
        html += '</table></div>';
    }
    
    // 非上升期基本信息统计
    if (data.declined && data.declined.summary) {
        const summary = data.declined.summary;
        html += '<div class="summary-box" style="flex: 1; min-width: 350px; max-width: 600px; background: #fff5f5; border-left: 4px solid #e24a4a;">';
        html += '<h6 style="margin-top: 0; color: #e24a4a; font-weight: bold;">非上升期</h6>';
        html += '<table style="width: 100%; border-collapse: collapse;">';
        html += `<tr><td style="padding: 4px 4px 4px 8px; width: 50%;">总记录数:</td><td style="padding: 4px 8px 4px 4px; text-align: right; font-weight: bold;">${(summary.total_records || 0).toLocaleString()} 条</td></tr>`;
        html += `<tr><td style="padding: 4px 4px 4px 8px;">去重商品ID数量:</td><td style="padding: 4px 8px 4px 4px; text-align: right; font-weight: bold;">${(summary.unique_goods || 0).toLocaleString()} 个</td></tr>`;
        if (summary.min_date && summary.max_date) {
            html += `<tr><td colspan="2" style="padding: 8px 8px 4px 8px; font-weight: bold; border-top: 1px solid #ddd;">时间周期:</td></tr>`;
            html += `<tr><td style="padding: 4px 4px 4px 20px;">最早日期:</td><td style="padding: 4px 8px 4px 4px; text-align: right;">${summary.min_date}</td></tr>`;
            html += `<tr><td style="padding: 4px 4px 4px 20px;">最晚日期:</td><td style="padding: 4px 8px 4px 4px; text-align: right;">${summary.max_date}</td></tr>`;
            html += `<tr><td style="padding: 4px 4px 4px 20px;">时间跨度:</td><td style="padding: 4px 8px 4px 4px; text-align: right; font-weight: bold;">${summary.date_range} 天</td></tr>`;
        }
        html += '</table></div>';
    }
    
    html += '</div>'; // 结束flex容器
    
    // 汇总基本信息统计
    if (data.total_summary) {
        const summary = data.total_summary;
        html += '<div style="margin-top: 15px; display: flex; gap: 15px; align-items: flex-start; flex-wrap: wrap;">';
        html += '<div class="summary-box" style="background: #f9f9f9; border-left: 4px solid #666; flex: 1; min-width: 300px; max-width: 500px;">';
        html += '<h6 style="margin-top: 0; color: #333; font-weight: bold;">汇总</h6>';
        html += '<table style="width: 100%; border-collapse: collapse;">';
        html += `<tr><td style="padding: 4px 8px; width: auto; white-space: nowrap;">总记录数:</td><td style="padding: 4px 8px; text-align: right; font-weight: bold; width: 100%;">${(summary.total_records || 0).toLocaleString()} 条</td></tr>`;
        html += `<tr><td style="padding: 4px 8px; white-space: nowrap;">去重商品ID数量:</td><td style="padding: 4px 8px; text-align: right; font-weight: bold;">${(summary.unique_goods || 0).toLocaleString()} 个</td></tr>`;
        if (summary.min_date && summary.max_date) {
            html += `<tr><td colspan="2" style="padding: 8px 8px 4px 8px; font-weight: bold; border-top: 1px solid #ddd;">时间周期:</td></tr>`;
            html += `<tr><td style="padding: 4px 8px; padding-left: 20px; white-space: nowrap;">最早日期:</td><td style="padding: 4px 8px; text-align: right;">${summary.min_date}</td></tr>`;
            html += `<tr><td style="padding: 4px 8px; padding-left: 20px; white-space: nowrap;">最晚日期:</td><td style="padding: 4px 8px; text-align: right;">${summary.max_date}</td></tr>`;
            html += `<tr><td style="padding: 4px 8px; padding-left: 20px; white-space: nowrap;">时间跨度:</td><td style="padding: 4px 8px; text-align: right; font-weight: bold;">${summary.date_range} 天</td></tr>`;
        }
        // 显示Reason类别统计
        if (summary.out_of_stock_count !== undefined || summary.secondary_traffic_restricted_count !== undefined || 
            summary.blocked_count !== undefined || summary.normal_count !== undefined || summary.none_count !== undefined) {
            html += `<tr><td colspan="2" style="padding: 8px 8px 4px 8px; font-weight: bold; border-top: 1px solid #ddd;">Reason类别统计:</td></tr>`;
            html += `<tr><td style="padding: 4px 8px; padding-left: 20px; white-space: nowrap;">Out_of_stock数量:</td><td style="padding: 4px 8px; text-align: right; font-weight: bold;">${(summary.out_of_stock_count || 0).toLocaleString()} 个</td></tr>`;
            html += `<tr><td style="padding: 4px 8px; padding-left: 20px; white-space: nowrap;">Secondary_traffic_restricted数量:</td><td style="padding: 4px 8px; text-align: right; font-weight: bold;">${(summary.secondary_traffic_restricted_count || 0).toLocaleString()} 个</td></tr>`;
            html += `<tr><td style="padding: 4px 8px; padding-left: 20px; white-space: nowrap;">Blocked数量:</td><td style="padding: 4px 8px; text-align: right; font-weight: bold;">${(summary.blocked_count || 0).toLocaleString()} 个</td></tr>`;
            html += `<tr><td style="padding: 4px 8px; padding-left: 20px; white-space: nowrap;">Normal数量:</td><td style="padding: 4px 8px; text-align: right; font-weight: bold;">${(summary.normal_count || 0).toLocaleString()} 个</td></tr>`;
            html += `<tr><td style="padding: 4px 8px; padding-left: 20px; white-space: nowrap;">None数量:</td><td style="padding: 4px 8px; text-align: right; font-weight: bold;">${(summary.none_count || 0).toLocaleString()} 个</td></tr>`;
        }
        // 显示在售占比
        if (summary.on_sale_ratio !== undefined) {
            html += `<tr><td style="padding: 8px 8px 4px 8px; font-weight: bold; border-top: 1px solid #ddd; white-space: nowrap;">在售占比:</td><td style="padding: 8px 8px 4px 8px; text-align: right; font-weight: bold; border-top: 1px solid #ddd;">${summary.on_sale_ratio.toFixed(2)}%</td></tr>`;
        }
        html += '</table></div>';
        
        // 显示Reason类别饼图（放在右边）
        if (summary.reason_pie_chart) {
            html += '<div class="summary-box" style="background: #f9f9f9; border-left: 4px solid #666; flex: 1; min-width: 350px; max-width: 600px; text-align: center; align-self: flex-start;">';
            html += '<h6 style="margin-top: 0; color: #333; font-weight: bold;">Reason类别分布</h6>';
            html += `<img src="data:image/png;base64,${summary.reason_pie_chart}" alt="Reason类别统计饼图" style="max-width: 100%; height: auto; width: 100%;">`;
            html += '</div>';
        }
        
        html += '</div>'; // 结束flex容器
    }
    
    html += '</div>'; // 结束基本信息统计容器
    
    resultDiv.innerHTML = html;
}

// 从缓存显示功能2的结果（不包含图片）
function displayFunction2ResultFromCache(data) {
    const resultDiv = document.getElementById('function2-result');
    let html = '<h5>分析结果（来自缓存，图片需重新分析获取）</h5>';
    
    // 统计信息
    if (data.statistics) {
        const stats = data.statistics;
        html += '<div class="summary-box" style="background: #f8f9fa; border-left: 4px solid #0d6efd; max-width: 600px;">';
        html += '<h6 style="margin-top: 0; color: #0d6efd; font-weight: bold;">统计信息</h6>';
        html += '<table style="width: 100%; border-collapse: collapse;">';
        html += `<tr><td style="padding: 4px 8px; width: auto; white-space: nowrap;"><strong>日期：</strong></td><td style="padding: 4px 8px; text-align: right; font-weight: bold; width: 100%;">${stats.date}</td></tr>`;
        html += `<tr><td colspan="2" style="padding: 8px 8px 4px 8px; font-weight: bold; border-top: 1px solid #ddd;">上升期统计:</td></tr>`;
        html += `<tr><td style="padding: 4px 8px; padding-left: 20px; white-space: nowrap;">前一天上升期:</td><td style="padding: 4px 8px; text-align: right; font-weight: bold;">${stats.previous_rising_count || 0}个</td></tr>`;
        html += `<tr><td style="padding: 4px 8px; padding-left: 20px; white-space: nowrap;">计算上升期:</td><td style="padding: 4px 8px; text-align: right; font-weight: bold;">${stats.calculated_rising_count || stats.rising_count}个</td></tr>`;
        html += `<tr><td style="padding: 4px 8px; padding-left: 20px; white-space: nowrap;">实际上升期:</td><td style="padding: 4px 8px; text-align: right; font-weight: bold; color: #198754;">${stats.rising_count}个</td></tr>`;
        html += `<tr><td colspan="2" style="padding: 8px 8px 4px 8px; font-weight: bold; border-top: 1px solid #ddd;">非上升期统计:</td></tr>`;
        html += `<tr><td style="padding: 4px 8px; padding-left: 20px; white-space: nowrap;">非上升期:</td><td style="padding: 4px 8px; text-align: right; font-weight: bold;">${stats.declined_count}个</td></tr>`;
        html += `<tr><td colspan="2" style="padding: 8px 8px 4px 8px; font-weight: bold; border-top: 1px solid #ddd;">变更统计:</td></tr>`;
        html += `<tr><td style="padding: 4px 8px; padding-left: 20px; white-space: nowrap;">新增上升期:</td><td style="padding: 4px 8px; text-align: right; font-weight: bold;">${stats.new_rising}个</td></tr>`;
        html += `<tr><td style="padding: 4px 8px; padding-left: 20px; white-space: nowrap;">新增非上升期:</td><td style="padding: 4px 8px; text-align: right; font-weight: bold;">${stats.new_declined}个</td></tr>`;
        html += `<tr><td style="padding: 4px 8px; padding-left: 20px; white-space: nowrap;">更新为上升期:</td><td style="padding: 4px 8px; text-align: right; font-weight: bold;">${stats.updated_to_rising}个</td></tr>`;
        html += `<tr><td style="padding: 4px 8px; padding-left: 20px; white-space: nowrap;">由非上升期重回上升期:</td><td style="padding: 4px 8px; text-align: right; font-weight: bold;">${stats.back_to_rising}个</td></tr>`;
        html += `<tr><td style="padding: 4px 8px; padding-left: 20px; color: #dc3545; white-space: nowrap;"><strong>！！！由上升期到非上升期:</strong></td><td style="padding: 4px 8px; text-align: right; font-weight: bold; color: #dc3545;">${stats.declined_from_rising}个</td></tr>`;
        html += '</table></div>';
    }
    
    const stats = data.statistics || {};
    const categories = data.categories || {};
    const allCategoryGoodsIds = new Set();
    
    // 收集所有已显示的类别goods_id
    if (stats.new_rising_goods) stats.new_rising_goods.forEach(id => allCategoryGoodsIds.add(id));
    if (stats.new_declined_goods) stats.new_declined_goods.forEach(id => allCategoryGoodsIds.add(id));
    if (stats.updated_to_rising_goods) stats.updated_to_rising_goods.forEach(id => allCategoryGoodsIds.add(id));
    if (stats.back_to_rising_goods) stats.back_to_rising_goods.forEach(id => allCategoryGoodsIds.add(id));
    if (stats.declined_from_rising_goods) stats.declined_from_rising_goods.forEach(id => allCategoryGoodsIds.add(id));
    
    // 辅助函数：显示商品信息（缓存版本，无图片）
    function displayGoodsSectionFromCache(title, goodsInfo) {
        if (!goodsInfo || goodsInfo.length === 0) return '';
        
        let sectionHtml = `<h6><strong>▶ ${title}</strong></h6>`;
        sectionHtml += '<div class="summary-box"><p class="text-muted">提示：图片数据未缓存，请点击"分析"按钮重新获取图表</p></div>';
        sectionHtml += '<div class="goods-info-text-container" style="margin-bottom: 10px; padding: 10px; background: #f8f9fa; border-radius: 5px;">';
        goodsInfo.forEach(info => {
            sectionHtml += `<div style="margin: 5px 0; font-family: monospace; font-size: 14px;">${info.goods_id} - 加入时间: ${info.join_date}, Reason: ${info.reason}</div>`;
        });
        sectionHtml += '</div>';
        return sectionHtml;
    }
    
    // 1. 新增上升期（所有模块都显示数据）
    if (stats.new_rising > 0) {
        const categoryData = categories.new_rising || {};
        const categoryGoodsInfo = categoryData.goods_info || [];
        html += displayGoodsSectionFromCache(`新增上升期（上升期）：${stats.new_rising}个`, categoryGoodsInfo);
    }
    
    // 2. 新增非上升期（所有模块都显示数据）
    if (stats.new_declined > 0) {
        const categoryData = categories.new_declined || {};
        const categoryGoodsInfo = categoryData.goods_info || [];
        html += displayGoodsSectionFromCache(`新增非上升期（非上升期）：${stats.new_declined}个`, categoryGoodsInfo);
    }
    
    // 3. 更新为上升期（所有模块都显示数据）
    if (stats.updated_to_rising > 0) {
        const categoryData = categories.updated_to_rising || {};
        const categoryGoodsInfo = categoryData.goods_info || [];
        html += displayGoodsSectionFromCache(`更新为上升期（上升期）：${stats.updated_to_rising}个`, categoryGoodsInfo);
    }
    
    // 4. 由非上升期重回上升期（所有模块都显示数据）
    if (stats.back_to_rising > 0) {
        const categoryData = categories.back_to_rising || {};
        const categoryGoodsInfo = categoryData.goods_info || [];
        html += displayGoodsSectionFromCache(`由非上升期重回上升期（上升期）：${stats.back_to_rising}个`, categoryGoodsInfo);
    }
    
    // 5. 由上升期到非上升期（所有模块都显示数据）
    if (stats.declined_from_rising > 0) {
        const categoryData = categories.declined_from_rising || {};
        const categoryGoodsInfo = categoryData.goods_info || [];
        html += displayGoodsSectionFromCache(`由上升期到非上升期（非上升期）：${stats.declined_from_rising}个`, categoryGoodsInfo);
    }
    
    // 6. 上升期商品（剩余商品）
    if (data.rising && data.rising.goods_info && data.rising.goods_info.length > 0) {
        const remainingGoodsInfo = data.rising.goods_info.filter(info => !allCategoryGoodsIds.has(info.goods_id));
        if (remainingGoodsInfo.length > 0) {
            html += `<h6><strong>▶ 历史上升期商品：${remainingGoodsInfo.length}个</strong></h6>`;
            html += '<div class="summary-box"><p class="text-muted">提示：图片数据未缓存，请点击"分析"按钮重新获取图表</p></div>';
            html += '<div class="goods-info-text-container" style="margin-bottom: 10px; padding: 10px; background: #f8f9fa; border-radius: 5px;">';
            remainingGoodsInfo.forEach(info => {
                html += `<div style="margin: 5px 0; font-family: monospace; font-size: 14px;">${info.goods_id} - 加入时间: ${info.join_date}, Reason: ${info.reason}</div>`;
            });
            html += '</div>';
        }
    }
    
    // 7. 非上升期商品（剩余商品）
    if (data.declined && data.declined.goods_info && data.declined.goods_info.length > 0) {
        const remainingGoodsInfo = data.declined.goods_info.filter(info => !allCategoryGoodsIds.has(info.goods_id));
        if (remainingGoodsInfo.length > 0) {
            html += `<h6><strong>▶ 历史非上升期商品：${remainingGoodsInfo.length}个</strong></h6>`;
            html += '<div class="summary-box"><p class="text-muted">提示：图片数据未缓存，请点击"分析"按钮重新获取图表</p></div>';
            html += '<div class="goods-info-text-container" style="margin-bottom: 10px; padding: 10px; background: #f8f9fa; border-radius: 5px;">';
            remainingGoodsInfo.forEach(info => {
                html += `<div style="margin: 5px 0; font-family: monospace; font-size: 14px;">${info.goods_id} - 加入时间: ${info.join_date}, Reason: ${info.reason}</div>`;
            });
            html += '</div>';
        }
    }
    
    // 8. 基本信息统计（统一放在最后）
    html += '<div style="margin-top: 20px;"><h6><strong>▶ 基本信息统计</strong></h6>';
    
    // 使用表格布局美化显示
    html += '<div style="display: flex; gap: 15px; flex-wrap: wrap; margin-top: 10px;">';
    
    // 上升期基本信息统计
    if (data.rising && data.rising.summary) {
        const summary = data.rising.summary;
        html += '<div class="summary-box" style="flex: 1; min-width: 300px; max-width: 500px; background: #f0f8ff; border-left: 4px solid #4a90e2;">';
        html += '<h6 style="margin-top: 0; color: #4a90e2; font-weight: bold;">上升期</h6>';
        html += '<table style="width: 100%; border-collapse: collapse;">';
        html += `<tr><td style="padding: 4px 4px 4px 8px; width: 50%;">总记录数:</td><td style="padding: 4px 8px 4px 4px; text-align: right; font-weight: bold;">${(summary.total_records || 0).toLocaleString()} 条</td></tr>`;
        html += `<tr><td style="padding: 4px 4px 4px 8px;">去重商品ID数量:</td><td style="padding: 4px 8px 4px 4px; text-align: right; font-weight: bold;">${(summary.unique_goods || 0).toLocaleString()} 个</td></tr>`;
        if (summary.min_date && summary.max_date) {
            html += `<tr><td colspan="2" style="padding: 8px 8px 4px 8px; font-weight: bold; border-top: 1px solid #ddd;">时间周期:</td></tr>`;
            html += `<tr><td style="padding: 4px 4px 4px 20px;">最早日期:</td><td style="padding: 4px 8px 4px 4px; text-align: right;">${summary.min_date}</td></tr>`;
            html += `<tr><td style="padding: 4px 4px 4px 20px;">最晚日期:</td><td style="padding: 4px 8px 4px 4px; text-align: right;">${summary.max_date}</td></tr>`;
            html += `<tr><td style="padding: 4px 4px 4px 20px;">时间跨度:</td><td style="padding: 4px 8px 4px 4px; text-align: right; font-weight: bold;">${summary.date_range} 天</td></tr>`;
        }
        html += '</table></div>';
    }
    
    // 非上升期基本信息统计
    if (data.declined && data.declined.summary) {
        const summary = data.declined.summary;
        html += '<div class="summary-box" style="flex: 1; min-width: 350px; max-width: 600px; background: #fff5f5; border-left: 4px solid #e24a4a;">';
        html += '<h6 style="margin-top: 0; color: #e24a4a; font-weight: bold;">非上升期</h6>';
        html += '<table style="width: 100%; border-collapse: collapse;">';
        html += `<tr><td style="padding: 4px 4px 4px 8px; width: 50%;">总记录数:</td><td style="padding: 4px 8px 4px 4px; text-align: right; font-weight: bold;">${(summary.total_records || 0).toLocaleString()} 条</td></tr>`;
        html += `<tr><td style="padding: 4px 4px 4px 8px;">去重商品ID数量:</td><td style="padding: 4px 8px 4px 4px; text-align: right; font-weight: bold;">${(summary.unique_goods || 0).toLocaleString()} 个</td></tr>`;
        if (summary.min_date && summary.max_date) {
            html += `<tr><td colspan="2" style="padding: 8px 8px 4px 8px; font-weight: bold; border-top: 1px solid #ddd;">时间周期:</td></tr>`;
            html += `<tr><td style="padding: 4px 4px 4px 20px;">最早日期:</td><td style="padding: 4px 8px 4px 4px; text-align: right;">${summary.min_date}</td></tr>`;
            html += `<tr><td style="padding: 4px 4px 4px 20px;">最晚日期:</td><td style="padding: 4px 8px 4px 4px; text-align: right;">${summary.max_date}</td></tr>`;
            html += `<tr><td style="padding: 4px 4px 4px 20px;">时间跨度:</td><td style="padding: 4px 8px 4px 4px; text-align: right; font-weight: bold;">${summary.date_range} 天</td></tr>`;
        }
        html += '</table></div>';
    }
    
    html += '</div>'; // 结束flex容器
    
    // 汇总基本信息统计
    if (data.total_summary) {
        const summary = data.total_summary;
        html += '<div style="margin-top: 15px; display: flex; gap: 15px; align-items: flex-start; flex-wrap: wrap;">';
        html += '<div class="summary-box" style="background: #f9f9f9; border-left: 4px solid #666; flex: 1; min-width: 300px; max-width: 500px;">';
        html += '<h6 style="margin-top: 0; color: #333; font-weight: bold;">汇总</h6>';
        html += '<table style="width: 100%; border-collapse: collapse;">';
        html += `<tr><td style="padding: 4px 8px; width: auto; white-space: nowrap;">总记录数:</td><td style="padding: 4px 8px; text-align: right; font-weight: bold; width: 100%;">${(summary.total_records || 0).toLocaleString()} 条</td></tr>`;
        html += `<tr><td style="padding: 4px 8px; white-space: nowrap;">去重商品ID数量:</td><td style="padding: 4px 8px; text-align: right; font-weight: bold;">${(summary.unique_goods || 0).toLocaleString()} 个</td></tr>`;
        if (summary.min_date && summary.max_date) {
            html += `<tr><td colspan="2" style="padding: 8px 8px 4px 8px; font-weight: bold; border-top: 1px solid #ddd;">时间周期:</td></tr>`;
            html += `<tr><td style="padding: 4px 8px; padding-left: 20px; white-space: nowrap;">最早日期:</td><td style="padding: 4px 8px; text-align: right;">${summary.min_date}</td></tr>`;
            html += `<tr><td style="padding: 4px 8px; padding-left: 20px; white-space: nowrap;">最晚日期:</td><td style="padding: 4px 8px; text-align: right;">${summary.max_date}</td></tr>`;
            html += `<tr><td style="padding: 4px 8px; padding-left: 20px; white-space: nowrap;">时间跨度:</td><td style="padding: 4px 8px; text-align: right; font-weight: bold;">${summary.date_range} 天</td></tr>`;
        }
        // 显示Reason类别统计
        if (summary.out_of_stock_count !== undefined || summary.secondary_traffic_restricted_count !== undefined || 
            summary.blocked_count !== undefined || summary.normal_count !== undefined || summary.none_count !== undefined) {
            html += `<tr><td colspan="2" style="padding: 8px 8px 4px 8px; font-weight: bold; border-top: 1px solid #ddd;">Reason类别统计:</td></tr>`;
            html += `<tr><td style="padding: 4px 8px; padding-left: 20px; white-space: nowrap;">Out_of_stock数量:</td><td style="padding: 4px 8px; text-align: right; font-weight: bold;">${(summary.out_of_stock_count || 0).toLocaleString()} 个</td></tr>`;
            html += `<tr><td style="padding: 4px 8px; padding-left: 20px; white-space: nowrap;">Secondary_traffic_restricted数量:</td><td style="padding: 4px 8px; text-align: right; font-weight: bold;">${(summary.secondary_traffic_restricted_count || 0).toLocaleString()} 个</td></tr>`;
            html += `<tr><td style="padding: 4px 8px; padding-left: 20px; white-space: nowrap;">Blocked数量:</td><td style="padding: 4px 8px; text-align: right; font-weight: bold;">${(summary.blocked_count || 0).toLocaleString()} 个</td></tr>`;
            html += `<tr><td style="padding: 4px 8px; padding-left: 20px; white-space: nowrap;">Normal数量:</td><td style="padding: 4px 8px; text-align: right; font-weight: bold;">${(summary.normal_count || 0).toLocaleString()} 个</td></tr>`;
            html += `<tr><td style="padding: 4px 8px; padding-left: 20px; white-space: nowrap;">None数量:</td><td style="padding: 4px 8px; text-align: right; font-weight: bold;">${(summary.none_count || 0).toLocaleString()} 个</td></tr>`;
        }
        // 显示在售占比
        if (summary.on_sale_ratio !== undefined) {
            html += `<tr><td style="padding: 8px 8px 4px 8px; font-weight: bold; border-top: 1px solid #ddd; white-space: nowrap;">在售占比:</td><td style="padding: 8px 8px 4px 8px; text-align: right; font-weight: bold; border-top: 1px solid #ddd;">${summary.on_sale_ratio.toFixed(2)}%</td></tr>`;
        }
        html += '</table></div>';
        
        // 显示Reason类别饼图（放在右边）
        if (summary.reason_pie_chart) {
            html += '<div class="summary-box" style="background: #f9f9f9; border-left: 4px solid #666; flex: 1; min-width: 350px; max-width: 600px; text-align: center; align-self: flex-start;">';
            html += '<h6 style="margin-top: 0; color: #333; font-weight: bold;">Reason类别分布</h6>';
            html += `<img src="data:image/png;base64,${summary.reason_pie_chart}" alt="Reason类别统计饼图" style="max-width: 100%; height: auto; width: 100%;">`;
            html += '</div>';
        }
        
        html += '</div>'; // 结束flex容器
    }
    
    html += '</div>'; // 结束基本信息统计容器
    
    resultDiv.innerHTML = html;
}

// 清除功能2的缓存
function clearFunction2Cache() {
    sessionStorage.removeItem('function2_cache');
    document.getElementById('function2-result').innerHTML = '<p class="text-muted">缓存已清除</p>';
}

function showExportFunction2Modal() {
    const modal = new bootstrap.Modal(document.getElementById('exportFunction2Modal'));
    modal.show();
}

function selectAllFields() {
    document.querySelectorAll('.field-checkbox').forEach(cb => cb.checked = true);
}

function deselectAllFields() {
    document.querySelectorAll('.field-checkbox').forEach(cb => cb.checked = false);
}

async function exportFunction2Data() {
    let targetDate = document.getElementById('target-date-input').value;
    // 如果没有输入日期，使用昨天
    if (!targetDate) {
        const yesterday = new Date();
        yesterday.setDate(yesterday.getDate() - 1);
        targetDate = yesterday.toISOString().split('T')[0];
    }
    
    // 获取导出选项
    const exportFormat = document.getElementById('export-format-select').value;
    const statusFilter = document.getElementById('status-filter-select').value;
    const dateRange = document.getElementById('date-range-select').value;
    
    // 获取选中的字段
    const selectedFields = [];
    document.querySelectorAll('.field-checkbox:checked').forEach(cb => {
        selectedFields.push(cb.value);
    });
    
    // 关闭模态框
    const modal = bootstrap.Modal.getInstance(document.getElementById('exportFunction2Modal'));
    if (modal) {
        modal.hide();
    }
    
    try {
        const response = await fetch('/api/function2/export', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                target_date: targetDate,
                export_format: exportFormat,
                status_filter: statusFilter,
                date_range: dateRange,
                selected_fields: selectedFields.length > 0 ? selectedFields : null
            })
        });
        
        if (response.ok) {
            const blob = await response.blob();
            const contentDisposition = response.headers.get('Content-Disposition');
            let filename = '动销品管理数据.' + exportFormat;
            if (contentDisposition && contentDisposition.indexOf('filename=') !== -1) {
                filename = decodeURIComponent(contentDisposition.split('filename=')[1].split(';')[0].replace(/"/g, ''));
            }
            
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            a.remove();
            window.URL.revokeObjectURL(url);
            alert('数据导出成功！');
        } else {
            const errorText = await response.text();
            try {
                const errorJson = JSON.parse(errorText);
                alert('数据导出失败: ' + errorJson.error);
            } catch (e) {
                alert('数据导出失败: ' + errorText);
            }
        }
    } catch (error) {
        alert('请求失败: ' + error.message);
    }
}

// 功能3：优化效果数据
function showFunction3() {
    // 隐藏功能6和功能7面板，显示功能内容区域
    const function6Content = document.getElementById('function6-content');
    if (function6Content) {
        function6Content.style.display = 'none';
    }
    const function7Content = document.getElementById('function7-content');
    if (function7Content) {
        function7Content.style.display = 'none';
    }
    const functionContent = document.getElementById('function-content');
    if (functionContent) {
        functionContent.style.display = 'block';
    }
    
    const content = `
        <h4>优化效果数据</h4>
        <div class="mb-3">
            <label class="form-label">选择类型:</label>
            <div class="btn-group" role="group">
                <button class="btn btn-primary" onclick="doOptimization('Video')">Video标记</button>
                <button class="btn btn-primary" onclick="doOptimization('Price')">Price标记</button>
            </div>
        </div>
        <div id="function3-result"></div>
    `;
    document.getElementById('function-content').innerHTML = content;
}

async function doOptimization(fieldName) {
    const resultDiv = document.getElementById('function3-result');
    resultDiv.innerHTML = '<p>正在查询...</p>';
    
    try {
        const response = await fetch('/api/function3/optimization', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ field_name: fieldName })
        });
        
        const result = await response.json();
        
        if (result.success) {
            const data = result.data;
            let html = `<h5>${fieldName}优化效果数据</h5>`;
            
            // 基本信息统计
            if (data.summary) {
                const summary = data.summary;
                html += '<div class="summary-box"><h6>基本信息统计</h6>';
                html += `<p>总记录数: ${(summary.total_records || 0).toLocaleString()} 条</p>`;
                html += `<p>去重商品ID数量: ${(summary.unique_goods || 0).toLocaleString()} 个</p>`;
                if (summary.date_range && summary.date_range !== 'N/A') {
                    html += `<p>时间范围: ${summary.date_range}</p>`;
                }
                html += '</div>';
            }
            
            // 按每行3个商品分组显示（类似功能2）
            if (data.images && data.images.length > 0 && data.goods_info && data.goods_info.length > 0) {
                const cols = 3;
                let goodsIndex = 0;
                
                data.images.forEach((img, imgIdx) => {
                    // 每张图片包含3个商品（最后一张可能少于3个）
                    const goodsInThisImage = Math.min(cols, data.goods_info.length - goodsIndex);
                    
                    // 在图片上方显示商品信息文字
                    html += '<div class="goods-info-text-container" style="margin-bottom: 10px; padding: 10px; background: #f8f9fa; border-radius: 5px;">';
                    for (let i = 0; i < goodsInThisImage && goodsIndex < data.goods_info.length; i++) {
                        const info = data.goods_info[goodsIndex];
                        html += `<div style="margin: 5px 0; font-family: monospace; font-size: 14px;">${info.goods_id} - 标记日期: ${info.marked_dates}</div>`;
                        goodsIndex++;
                    }
                    html += '</div>';
                    
                    // 显示图片
                    html += `<div class="image-container"><img src="data:image/png;base64,${img}" alt="${fieldName}图${imgIdx+1}"></div>`;
                });
            } else if (data.images && data.images.length > 0) {
                // 如果没有goods_info，只显示图片
                data.images.forEach((img, idx) => {
                    html += `<div class="image-container"><img src="data:image/png;base64,${img}" alt="${fieldName}图${idx+1}"></div>`;
                });
            }
            
            resultDiv.innerHTML = html;
        } else {
            resultDiv.innerHTML = `<div class="error-message">错误: ${result.error}</div>`;
        }
    } catch (error) {
        resultDiv.innerHTML = `<div class="error-message">请求失败: ${error.message}</div>`;
    }
}

// 功能4：手动更新记录
function showFunction4() {
    // 隐藏功能6和功能7面板，显示功能内容区域
    const function6Content = document.getElementById('function6-content');
    if (function6Content) {
        function6Content.style.display = 'none';
    }
    const function7Content = document.getElementById('function7-content');
    if (function7Content) {
        function7Content.style.display = 'none';
    }
    const functionContent = document.getElementById('function-content');
    if (functionContent) {
        functionContent.style.display = 'block';
    }
    
    // 设置默认日期为昨天
    const yesterday = new Date();
    yesterday.setDate(yesterday.getDate() - 1);
    const yesterdayStr = yesterday.toISOString().split('T')[0];
    
    const content = `
        <h4>手动更新记录</h4>
        
        <!-- 自动更新Reason区域 -->
        <div class="card mb-3">
            <div class="card-header bg-success text-dark">
                <strong>自动更新Reason</strong>
                <button class="btn btn-sm btn-light float-end" onclick="showAutoReasonConfigModal()">配置</button>
            </div>
            <div class="card-body">
                <div class="row">
                    <div class="col-md-8">
                        <p class="mb-2"><strong>功能说明：</strong>批量更新<strong>昨日</strong>所有动销品的Reason状态</p>
                        <p class="mb-2 text-muted small">
                            自动识别：缺货(Out_of_stock)、封禁(Blocked)、二次限流(Secondary_traffic_restricted)、正常(Normal)等状态
                        </p>
                        <p class="mb-2 text-muted small">
                            <strong>注意：</strong>只能更新昨日数据，如果昨日没有数据会报错。已有异常状态记录的商品不会被重复标记。
                        </p>
                    </div>
                    <div class="col-md-4 text-end">
                        <button class="btn btn-success btn-lg" onclick="doAutoUpdateReason()">自动更新Reason</button>
                    </div>
                </div>
                <div id="auto-reason-config-display" class="mt-2">
                    <small class="text-muted">限流数据目录: <span id="auto-reason-dir-display">未配置</span></small>
                </div>
            </div>
        </div>
        
        <div class="row">
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header">更新Reason（手动）</div>
                    <div class="card-body">
                        <div class="mb-3">
                            <label class="form-label">Goods ID:</label>
                            <input type="text" class="form-control" id="reason-goods-id" onblur="loadAvailableDates('reason')">
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Date Label (默认昨天):</label>
                            <div class="input-group mb-2">
                                <input type="date" class="form-control" id="reason-date" value="${yesterdayStr}">
                                <button class="btn btn-outline-secondary" onclick="setYesterday('reason')" type="button">使用昨天</button>
                            </div>
                            <select class="form-control" id="reason-date-select" onchange="selectDateFromList('reason')">
                                <option value="">-- 或从列表选择 --</option>
                            </select>
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Reason:</label>
                            <textarea class="form-control" id="reason-text" rows="3"></textarea>
                        </div>
                        <button class="btn btn-primary" onclick="updateReason()">更新</button>
                    </div>
                </div>
            </div>
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header">更新Video/Price</div>
                    <div class="card-body">
                        <div class="mb-3">
                            <label class="form-label">Goods ID:</label>
                            <input type="text" class="form-control" id="video-price-goods-id" onblur="loadAvailableDates('video-price')">
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Date Label (默认昨天):</label>
                            <div class="input-group mb-2">
                                <input type="date" class="form-control" id="video-price-date" value="${yesterdayStr}">
                                <button class="btn btn-outline-secondary" onclick="setYesterday('video-price')" type="button">使用昨天</button>
                            </div>
                            <select class="form-control" id="video-price-date-select" onchange="selectDateFromList('video-price')">
                                <option value="">-- 或从列表选择 --</option>
                            </select>
                        </div>
                        <div class="mb-3">
                            <button class="btn btn-warning me-2" onclick="updateVideo()">更新Video</button>
                            <button class="btn btn-danger" onclick="updatePrice()">更新Price</button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        <div id="function4-result" class="mt-3"></div>
        
        <!-- 自动更新Reason功能说明 -->
        <div class="card mt-3">
            <div class="card-header">
                <button class="btn btn-link text-decoration-none p-0" type="button" data-bs-toggle="collapse" data-bs-target="#autoReasonHelp">
                    ▼ 自动更新Reason功能说明
                </button>
            </div>
            <div id="autoReasonHelp" class="collapse">
                <div class="card-body">
                    <h6>Reason标记规则：</h6>
                    <ol>
                        <li><strong>Out_of_stock (MMDD)</strong> - 缺货：商品表中detail_status为'Out of stock'</li>
                        <li><strong>Blocked (MMDD)</strong> - 封禁：商品表中detail_status为'Blocked'</li>
                        <li><strong>Secondary_traffic_restricted (MMDD)</strong> - 二次限流：在限流数据xlsx文件中存在</li>
                        <li><strong>Normal (MMDD)</strong> - 正常：不属于上述任何异常状态</li>
                        <li><strong>Normal (Xxx_MMDD)</strong> - 恢复正常：之前有异常状态记录，现在恢复正常</li>
                        <li><strong>Normal (Blocking_MMDD)</strong> - 有风险的正常品：商品表中detail_status为'At Risk'（优先级最高）</li>
                    </ol>
                    <h6>重要规则：</h6>
                    <ul>
                        <li>对于异常状态（Out_of_stock/Blocked/Secondary_traffic_restricted），如果之前已有相同类型的记录，则跳过不更新</li>
                        <li>对于Normal状态，无论之前有没有记录都会更新</li>
                        <li>Normal优先级：Normal (Blocking_MMDD) &gt; Normal (Xxx_MMDD) &gt; Normal (MMDD)</li>
                        <li>MMDD为日期后缀，如0125表示1月25日</li>
                    </ul>
                    <h6>配置说明：</h6>
                    <p>需要配置"限流数据目录"，该目录下应包含各国家站点子目录（如ROA1_CZ），子目录中的xlsx文件为限流数据。</p>
                    <p>例如：<code>C:\\Users\\PC\\Desktop\\code\\核价\\二次限流\\ROA1_FR\\priceTemplate_xxx.xlsx</code></p>
                </div>
            </div>
        </div>
    `;
    document.getElementById('function-content').innerHTML = content;
    
    // 加载自动更新Reason配置
    loadAutoReasonConfig();
}

// 设置昨天日期
function setYesterday(type) {
    const yesterday = new Date();
    yesterday.setDate(yesterday.getDate() - 1);
    const dateStr = yesterday.toISOString().split('T')[0];
    
    if (type === 'reason') {
        document.getElementById('reason-date').value = dateStr;
    } else {
        document.getElementById('video-price-date').value = dateStr;
    }
}

// 从列表选择日期
function selectDateFromList(type) {
    const select = type === 'reason' 
        ? document.getElementById('reason-date-select')
        : document.getElementById('video-price-date-select');
    const dateInput = type === 'reason'
        ? document.getElementById('reason-date')
        : document.getElementById('video-price-date');
    
    if (select.value) {
        dateInput.value = select.value;
    }
}

// 加载可用日期列表
async function loadAvailableDates(type) {
    const goodsIdInput = type === 'reason'
        ? document.getElementById('reason-goods-id')
        : document.getElementById('video-price-goods-id');
    const select = type === 'reason'
        ? document.getElementById('reason-date-select')
        : document.getElementById('video-price-date-select');
    
    const goodsId = goodsIdInput.value.trim();
    
    if (!goodsId) {
        select.innerHTML = '<option value="">-- 或从列表选择 --</option>';
        return;
    }
    
    try {
        const response = await fetch(`/api/function4/available_dates?goods_id=${goodsId}`);
        const result = await response.json();
        
        if (result.success && result.dates && result.dates.length > 0) {
            select.innerHTML = '<option value="">-- 或从列表选择 --</option>';
            result.dates.forEach(date => {
                const option = document.createElement('option');
                option.value = date;
                option.textContent = date;
                select.appendChild(option);
            });
        } else {
            select.innerHTML = '<option value="">-- 无可用日期 --</option>';
        }
    } catch (error) {
        console.error('加载日期列表失败:', error);
        select.innerHTML = '<option value="">-- 加载失败 --</option>';
    }
}

async function updateReason() {
    const goodsId = document.getElementById('reason-goods-id').value.trim();
    const dateLabel = document.getElementById('reason-date').value;
    const reason = document.getElementById('reason-text').value.trim();
    
    if (!goodsId || !dateLabel || !reason) {
        alert('请填写所有字段');
        return;
    }
    
    const resultDiv = document.getElementById('function4-result');
    resultDiv.innerHTML = '<p>正在更新...</p>';
    
    try {
        const response = await fetch('/api/function4/update_reason', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                goods_id: goodsId,
                date_label: dateLabel,
                reason: reason
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            resultDiv.innerHTML = `<div class="success-message">${result.message}</div>`;
        } else {
            resultDiv.innerHTML = `<div class="error-message">错误: ${result.error}</div>`;
        }
    } catch (error) {
        resultDiv.innerHTML = `<div class="error-message">请求失败: ${error.message}</div>`;
    }
}

async function updateVideo() {
    const goodsId = document.getElementById('video-price-goods-id').value.trim();
    const dateLabel = document.getElementById('video-price-date').value;
    
    if (!goodsId || !dateLabel) {
        alert('请填写所有字段');
        return;
    }
    
    const resultDiv = document.getElementById('function4-result');
    resultDiv.innerHTML = '<p>正在更新...</p>';
    
    try {
        const response = await fetch('/api/function4/update_video', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                goods_id: goodsId,
                date_label: dateLabel
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            resultDiv.innerHTML = `<div class="success-message">${result.message}</div>`;
        } else {
            resultDiv.innerHTML = `<div class="error-message">错误: ${result.error}</div>`;
        }
    } catch (error) {
        resultDiv.innerHTML = `<div class="error-message">请求失败: ${error.message}</div>`;
    }
}

async function updatePrice() {
    const goodsId = document.getElementById('video-price-goods-id').value.trim();
    const dateLabel = document.getElementById('video-price-date').value;
    
    if (!goodsId || !dateLabel) {
        alert('请填写所有字段');
        return;
    }
    
    const resultDiv = document.getElementById('function4-result');
    resultDiv.innerHTML = '<p>正在更新...</p>';
    
    try {
        const response = await fetch('/api/function4/update_price', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                goods_id: goodsId,
                date_label: dateLabel
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            resultDiv.innerHTML = `<div class="success-message">${result.message}</div>`;
        } else {
            resultDiv.innerHTML = `<div class="error-message">错误: ${result.error}</div>`;
        }
    } catch (error) {
        resultDiv.innerHTML = `<div class="error-message">请求失败: ${error.message}</div>`;
    }
}

// ===== 自动更新Reason相关函数 =====

// 加载自动更新Reason配置
async function loadAutoReasonConfig() {
    try {
        const response = await fetch('/api/function4/auto_reason_config');
        const result = await response.json();
        
        if (result.success) {
            const dirDisplay = document.getElementById('auto-reason-dir-display');
            if (dirDisplay) {
                const dir = result.data.traffic_restricted_data_dir;
                dirDisplay.textContent = dir ? dir : '未配置';
                dirDisplay.className = dir ? 'text-success' : 'text-danger';
            }
        }
    } catch (error) {
        console.error('加载自动更新Reason配置失败:', error);
    }
}

// 显示自动更新Reason配置模态框
function showAutoReasonConfigModal() {
    // 创建模态框HTML
    let modal = document.getElementById('autoReasonConfigModal');
    if (!modal) {
        const modalHtml = `
            <div class="modal fade" id="autoReasonConfigModal" tabindex="-1">
                <div class="modal-dialog">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">配置自动更新Reason</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <div class="mb-3">
                                <label class="form-label">限流数据目录:</label>
                                <input type="text" class="form-control" id="auto-reason-restricted-dir" 
                                    placeholder="例如: C:\\Users\\PC\\Desktop\\code\\核价\\二次限流">
                                <small class="text-muted">
                                    该目录下应包含各国家站点子目录（如ROA1_CZ），子目录中的xlsx文件为限流数据
                                </small>
                            </div>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">取消</button>
                            <button type="button" class="btn btn-primary" onclick="saveAutoReasonConfig()">保存配置</button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        document.body.insertAdjacentHTML('beforeend', modalHtml);
        modal = document.getElementById('autoReasonConfigModal');
    }
    
    // 加载当前配置到输入框
    loadAutoReasonConfigToModal();
    
    // 显示模态框
    const bsModal = new bootstrap.Modal(modal);
    bsModal.show();
}

// 加载配置到模态框
async function loadAutoReasonConfigToModal() {
    try {
        const response = await fetch('/api/function4/auto_reason_config');
        const result = await response.json();
        
        if (result.success) {
            document.getElementById('auto-reason-restricted-dir').value = result.data.traffic_restricted_data_dir || '';
        }
    } catch (error) {
        console.error('加载配置到模态框失败:', error);
    }
}

// 保存自动更新Reason配置
async function saveAutoReasonConfig() {
    const restrictedDir = document.getElementById('auto-reason-restricted-dir').value.trim();
    
    if (!restrictedDir) {
        alert('请填写限流数据目录');
        return;
    }
    
    try {
        const response = await fetch('/api/function4/auto_reason_config', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                traffic_restricted_data_dir: restrictedDir
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            showNotification('配置成功', 'success');
            bootstrap.Modal.getInstance(document.getElementById('autoReasonConfigModal')).hide();
            
            // 刷新配置显示
            loadAutoReasonConfig();
        } else {
            alert('配置失败: ' + result.error);
        }
    } catch (error) {
        console.error('保存配置失败:', error);
        alert('保存配置失败，请检查网络连接');
    }
}

// 执行自动更新Reason
async function doAutoUpdateReason() {
    const resultDiv = document.getElementById('function4-result');
    resultDiv.innerHTML = '<p><strong>正在自动更新Reason，请稍候...</strong></p>';
    
    try {
        const response = await fetch('/api/function4/auto_update_reason', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        const result = await response.json();
        
        if (result.success) {
            // 构建详细的结果显示
            const stats = result.stats;
            const dataSources = result.data_sources;
            
            let html = `
                <div class="alert alert-success">
                    <h5>✓ 自动更新Reason完成</h5>
                    <p><strong>目标日期：</strong>${result.target_date} (后缀: ${result.date_suffix})</p>
                    <p><strong>表名：</strong>${result.table_name}</p>
                </div>
                <div class="card">
                    <div class="card-header">更新统计</div>
                    <div class="card-body">
                        <table class="table table-sm table-bordered">
                            <thead>
                                <tr>
                                    <th>类别</th>
                                    <th>数量</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr><td>基础动销品数量</td><td>${stats.base_goods_count}</td></tr>
                                <tr class="table-danger"><td>缺货 (Out_of_stock)</td><td>${stats.out_of_stock}</td></tr>
                                <tr class="table-danger"><td>封禁 (Blocked)</td><td>${stats.blocked}</td></tr>
                                <tr class="table-warning"><td>二次限流 (Secondary_traffic_restricted)</td><td>${stats.secondary_traffic_restricted}</td></tr>
                                <tr class="table-success"><td>正常 (Normal)</td><td>${stats.normal}</td></tr>
                                <tr class="table-info"><td>恢复正常 (Normal Xxx)</td><td>${stats.normal_recovered}</td></tr>
                                <tr class="table-info"><td>有风险的正常品 (Normal Blocking)</td><td>${stats.normal_blocking}</td></tr>
                                <tr class="table-secondary"><td>跳过（已有异常记录）</td><td>${stats.skipped}</td></tr>
                                <tr class="table-danger"><td>缺货回填（昨日无数据）</td><td>${stats.out_of_stock_backfill ?? 0}</td></tr>
                                <tr class="table-danger"><td>封禁回填（昨日无数据）</td><td>${stats.blocked_backfill ?? 0}</td></tr>
                                <tr class="table-primary"><td><strong>成功更新</strong></td><td><strong>${stats.total_updated}</strong></td></tr>
                                <tr class="table-success"><td>总Normal</td><td>${(stats.normal ?? 0) + (stats.normal_recovered ?? 0) + (stats.normal_blocking ?? 0)}</td></tr>
                            </tbody>
                        </table>
                    </div>
                </div>
                <div class="card mt-2">
                    <div class="card-header">数据来源统计</div>
                    <div class="card-body">
                        <ul class="mb-0">
                            <li>商品表缺货数量: ${dataSources.out_of_stock_goods_count}</li>
                            <li>商品表封禁数量: ${dataSources.blocked_goods_count}</li>
                            <li>商品表有风险数量: ${dataSources.at_risk_goods_count}</li>
                            <li>限流数据xlsx数量: ${dataSources.restricted_goods_count}</li>
                        </ul>
                    </div>
                </div>
            `;
            
            resultDiv.innerHTML = html;
        } else {
            resultDiv.innerHTML = `<div class="alert alert-danger">错误: ${result.error}</div>`;
        }
    } catch (error) {
        resultDiv.innerHTML = `<div class="alert alert-danger">请求失败: ${error.message}</div>`;
    }
}

// 功能5：数据筛选
function showFunction5() {
    // 隐藏功能6和功能7面板，显示功能内容区域
    const function6Content = document.getElementById('function6-content');
    if (function6Content) {
        function6Content.style.display = 'none';
    }
    const function7Content = document.getElementById('function7-content');
    if (function7Content) {
        function7Content.style.display = 'none';
    }
    const functionContent = document.getElementById('function-content');
    if (functionContent) {
        functionContent.style.display = 'block';
    }
    
    const content = `
        <h4>数据筛选</h4>
        <div class="card mb-3">
            <div class="card-body">
                <div class="row">
                    <div class="col-md-3">
                        <label class="form-label">日期从:</label>
                        <input type="date" class="form-control" id="filter-date-from">
                    </div>
                    <div class="col-md-3">
                        <label class="form-label">日期到:</label>
                        <input type="date" class="form-control" id="filter-date-to">
                    </div>
                    <div class="col-md-3">
                        <label class="form-label">曝光量范围:</label>
                        <input type="number" class="form-control mb-2" id="filter-impressions-min" placeholder="最小值">
                        <input type="number" class="form-control" id="filter-impressions-max" placeholder="最大值">
                    </div>
                    <div class="col-md-3">
                        <label class="form-label">点击量范围:</label>
                        <input type="number" class="form-control mb-2" id="filter-clicks-min" placeholder="最小值">
                        <input type="number" class="form-control" id="filter-clicks-max" placeholder="最大值">
                    </div>
                </div>
                <div class="row mt-3">
                    <div class="col-md-3">
                        <label class="form-label">CTR范围:</label>
                        <input type="number" step="0.01" class="form-control mb-2" id="filter-ctr-min" placeholder="最小值">
                        <input type="number" step="0.01" class="form-control" id="filter-ctr-max" placeholder="最大值">
                    </div>
                    <div class="col-md-3">
                        <label class="form-label">排序字段:</label>
                        <select class="form-control" id="sort-field">
                            <option value="">无排序</option>
                            <option value="date_label">日期</option>
                            <option value="Product impressions">曝光量</option>
                            <option value="Product clicks">点击量</option>
                            <option value="CTR">CTR</option>
                        </select>
                    </div>
                    <div class="col-md-3">
                        <label class="form-label">排序方式:</label>
                        <select class="form-control" id="sort-order">
                            <option value="asc">递增</option>
                            <option value="desc">递减</option>
                        </select>
                    </div>
                    <div class="col-md-3">
                        <label class="form-label">&nbsp;</label>
                        <div class="form-check mb-2">
                            <input class="form-check-input" type="checkbox" id="mean-mode-checkbox">
                            <label class="form-check-label" for="mean-mode-checkbox">
                                <strong>均值模式</strong>（按goods_id取均值）
                            </label>
                        </div>
                        <div class="form-check mb-2">
                            <input class="form-check-input" type="checkbox" id="on-shelf-filter-checkbox">
                            <label class="form-check-label" for="on-shelf-filter-checkbox">
                                <strong>上架时间筛选模式</strong>（按上架日期筛选）
                            </label>
                        </div>
                        <button class="btn btn-primary w-100 mb-2" onclick="doDataFilter()">筛选</button>
                        <button class="btn btn-success w-100" onclick="exportFilteredData()">导出数据</button>
                    </div>
                </div>
            </div>
        </div>
        <div id="function5-result"></div>
    `;
    document.getElementById('function-content').innerHTML = content;
}

async function doDataFilter() {
    const filters = {
        date_from: document.getElementById('filter-date-from').value || null,
        date_to: document.getElementById('filter-date-to').value || null,
        impressions_min: document.getElementById('filter-impressions-min').value || null,
        impressions_max: document.getElementById('filter-impressions-max').value || null,
        clicks_min: document.getElementById('filter-clicks-min').value || null,
        clicks_max: document.getElementById('filter-clicks-max').value || null,
        ctr_min: document.getElementById('filter-ctr-min').value || null,
        ctr_max: document.getElementById('filter-ctr-max').value || null
    };
    
    const sortField = document.getElementById('sort-field').value || null;
    const sortOrder = document.getElementById('sort-order').value;
    const meanMode = document.getElementById('mean-mode-checkbox').checked;
    const onShelfFilterMode = document.getElementById('on-shelf-filter-checkbox').checked;
    
    const resultDiv = document.getElementById('function5-result');
    resultDiv.innerHTML = '<p>正在筛选...</p>';
    
    try {
        const response = await fetch('/api/function5/filter', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                filters: filters,
                sort_field: sortField,
                sort_order: sortOrder,
                page: 1,
                per_page: 100,
                mean_mode: meanMode,
                on_shelf_filter_mode: onShelfFilterMode
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            const data = result.data;
            let modeText = '';
            if (meanMode && onShelfFilterMode) {
                modeText = '（均值模式 + 上架时间筛选模式）';
            } else if (meanMode) {
                modeText = '（均值模式）';
            } else if (onShelfFilterMode) {
                modeText = '（上架时间筛选模式）';
            }
            let html = `<h5>筛选结果${modeText} (共 ${data.total} 条记录)</h5>`;
            
            if (data.records && data.records.length > 0) {
                html += '<div class="table-responsive"><table class="table table-striped table-bordered">';
                html += '<thead><tr>';
                const columns = Object.keys(data.records[0]);
                columns.forEach(col => {
                    html += `<th>${col}</th>`;
                });
                html += '</tr></thead><tbody>';
                
                data.records.forEach(record => {
                    html += '<tr>';
                    columns.forEach(col => {
                        const value = record[col];
                        html += `<td>${value !== null && value !== undefined ? value : ''}</td>`;
                    });
                    html += '</tr>';
                });
                
                html += '</tbody></table></div>';
            } else {
                html += '<p class="text-muted">没有找到匹配的记录</p>';
            }
            
            resultDiv.innerHTML = html;
        } else {
            resultDiv.innerHTML = `<div class="error-message">错误: ${result.error}</div>`;
        }
    } catch (error) {
        resultDiv.innerHTML = `<div class="error-message">请求失败: ${error.message}</div>`;
    }
}

// 导出筛选数据
async function exportFilteredData() {
    // 先确认是否要导出
    const exportFormat = confirm('选择导出格式：\n点击"确定"导出为Excel格式\n点击"取消"导出为CSV格式') ? 'excel' : 'csv';
    
    const filters = {
        date_from: document.getElementById('filter-date-from').value || null,
        date_to: document.getElementById('filter-date-to').value || null,
        impressions_min: document.getElementById('filter-impressions-min').value || null,
        impressions_max: document.getElementById('filter-impressions-max').value || null,
        clicks_min: document.getElementById('filter-clicks-min').value || null,
        clicks_max: document.getElementById('filter-clicks-max').value || null,
        ctr_min: document.getElementById('filter-ctr-min').value || null,
        ctr_max: document.getElementById('filter-ctr-max').value || null
    };
    
    const sortField = document.getElementById('sort-field').value || null;
    const sortOrder = document.getElementById('sort-order').value;
    const meanMode = document.getElementById('mean-mode-checkbox').checked;
    const onShelfFilterMode = document.getElementById('on-shelf-filter-checkbox').checked;
    
    try {
        const response = await fetch('/api/function5/export', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                filters: filters,
                sort_field: sortField,
                sort_order: sortOrder,
                export_format: exportFormat,
                mean_mode: meanMode,
                on_shelf_filter_mode: onShelfFilterMode
            })
        });
        
        if (!response.ok) {
            const error = await response.json();
            alert('导出失败: ' + (error.error || '未知错误'));
            return;
        }
        
        // 获取文件名
        const contentDisposition = response.headers.get('Content-Disposition');
        let filename = exportFormat === 'excel' ? '筛选数据.xlsx' : '筛选数据.csv';
        if (contentDisposition) {
            const filenameMatch = contentDisposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/);
            if (filenameMatch && filenameMatch[1]) {
                filename = filenameMatch[1].replace(/['"]/g, '');
                // 处理UTF-8编码的文件名
                if (filename.startsWith('UTF-8\'\'')) {
                    filename = decodeURIComponent(filename.replace('UTF-8\'\'', ''));
                }
            }
        }
        
        // 下载文件
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        
        alert('导出成功！文件已下载到本地。');
    } catch (error) {
        alert('导出失败: ' + error.message);
    }
}

// 切换特殊说明的显示/隐藏
function toggleSpecialNotes(id) {
    const element = document.getElementById(id);
    if (element) {
        element.style.display = element.style.display === 'none' ? 'block' : 'none';
    }
}

// 切换功能说明的显示/隐藏
function toggleFunction2Help(id) {
    const element = document.getElementById(id);
    if (element) {
        element.style.display = element.style.display === 'none' ? 'block' : 'none';
    }
}

// 切换缺失信息的显示/隐藏
function toggleMissingInfo(id) {
    const element = document.getElementById(id);
    if (element) {
        element.style.display = element.style.display === 'none' ? 'block' : 'none';
    }
}

// 性能优化工具函数
const performanceUtils = {
    // 防抖函数
    debounce: function(func, wait, immediate) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                timeout = null;
                if (!immediate) func(...args);
            };
            const callNow = immediate && !timeout;
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
            if (callNow) func(...args);
        };
    },

    // 节流函数
    throttle: function(func, limit) {
        let inThrottle;
        return function() {
            const args = arguments;
            const context = this;
            if (!inThrottle) {
                func.apply(context, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        }
    },

    // 懒加载图片
    lazyLoadImages: function() {
        const images = document.querySelectorAll('img[data-src]');
        const imageObserver = new IntersectionObserver((entries, observer) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    img.src = img.dataset.src;
                    img.classList.remove('lazy');
                    imageObserver.unobserve(img);
                }
            });
        });

        images.forEach(img => imageObserver.observe(img));
    }
};

// ===== 功能6：指标计算 =====

// 显示功能6
function showFunction6() {
    // 隐藏默认功能内容区域
    const functionContent = document.getElementById('function-content');
    if (functionContent) {
        functionContent.style.display = 'none';
    }

    // 隐藏所有功能面板
    document.querySelectorAll('.function-panel').forEach(panel => {
        panel.style.display = 'none';
    });

    // 显示功能6面板
    document.getElementById('function6-content').style.display = 'block';

    // 设置默认日期为昨天
    const yesterday = new Date();
    yesterday.setDate(yesterday.getDate() - 1);
    const yesterdayStr = yesterday.toISOString().split('T')[0];
    const dateInput = document.getElementById('indicator-date-input');
    if (dateInput) {
        dateInput.value = yesterdayStr;
    }

    // 加载指标配置
    loadIndicatorConfig();
}

// 显示指标配置模态框
function showIndicatorConfigModal() {
    loadIndicatorConfig();
    const modal = new bootstrap.Modal(document.getElementById('indicatorConfigModal'));
    modal.show();
}

// 加载指标配置
async function loadIndicatorConfig() {
    try {
        const response = await fetch('/api/function6/config');
        const result = await response.json();

        if (result.success) {
            document.getElementById('unpriced-data-dir').value = result.data.unpriced_data_dir || '';
            document.getElementById('traffic-restricted-data-dir').value = result.data.traffic_restricted_data_dir || '';
        }
    } catch (error) {
        console.error('加载指标配置失败:', error);
    }
}

// 保存指标配置
async function saveIndicatorConfig() {
    const unpricedDir = document.getElementById('unpriced-data-dir').value.trim();
    const restrictedDir = document.getElementById('traffic-restricted-data-dir').value.trim();

    if (!unpricedDir || !restrictedDir) {
        alert('请填写所有必需的目录路径');
        return;
    }

    try {
        const response = await fetch('/api/function6/config', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                unpriced_data_dir: unpricedDir,
                traffic_restricted_data_dir: restrictedDir
            })
        });

        const result = await response.json();

        if (result.success) {
            showNotification('配置成功', 'success');
            bootstrap.Modal.getInstance(document.getElementById('indicatorConfigModal')).hide();

            // 重新加载配置显示
            loadIndicatorConfig();
        } else {
            alert('配置失败: ' + result.error);
        }
    } catch (error) {
        console.error('保存配置失败:', error);
        alert('保存配置失败，请检查网络连接');
    }
}

// 设置指标日期为昨天
function setIndicatorDateToYesterday() {
    const yesterday = new Date();
    yesterday.setDate(yesterday.getDate() - 1);
    const yesterdayStr = yesterday.toISOString().split('T')[0];
    const dateInput = document.getElementById('indicator-date-input');
    if (dateInput) {
        dateInput.value = yesterdayStr;
    }
}

// 计算指标
async function calculateIndicators() {
    // 获取选择的日期
    const dateInput = document.getElementById('indicator-date-input');
    const targetDate = dateInput ? dateInput.value : null;
    
    if (!targetDate) {
        alert('请选择查询日期');
        return;
    }
    
    // 获取非缓存模式选项
    const noCache = document.getElementById('indicator-no-cache-checkbox').checked;
    const useCache = !noCache;  // 非缓存模式时，use_cache为false
    
    // 显示加载状态
    document.getElementById('indicators-loading').style.display = 'block';
    document.getElementById('indicators-empty').style.display = 'none';
    document.getElementById('indicators-results').style.display = 'none';
    document.getElementById('charts-container').style.display = 'none';

    try {
        const response = await fetch('/api/function6/indicators', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ 
                target_date: targetDate,
                use_cache: useCache
            })
        });
        const result = await response.json();

        if (result.success) {
            displayIndicators(result.data, result.analysis_time, result.from_cache);
        } else {
            let errorMsg = '计算指标失败: ' + result.error;
            if (result.analysis_time !== undefined && result.analysis_time !== null) {
                errorMsg += `\n计算耗时: ${result.analysis_time} 秒`;
            }
            alert(errorMsg);
            // 恢复空状态
            document.getElementById('indicators-empty').style.display = 'block';
        }
    } catch (error) {
        console.error('计算指标失败:', error);
        alert('计算指标失败，请检查网络连接');
        // 恢复空状态
        document.getElementById('indicators-empty').style.display = 'block';
    } finally {
        // 隐藏加载状态
        document.getElementById('indicators-loading').style.display = 'none';
    }
}

// 保存指标数据
async function saveIndicatorData() {
    // 获取选择的日期
    const dateInput = document.getElementById('indicator-date-input');
    const targetDate = dateInput ? dateInput.value : null;
    
    if (!targetDate) {
        alert('请选择查询日期');
        return;
    }
    
    // 显示保存中提示（不设置duration，让其持续显示）
    showNotification('保存中...', 'info', 0);
    
    try {
        const response = await fetch('/api/function6/save', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ target_date: targetDate })
        });
        
        // 清除"保存中"通知
        clearNotifications();
        
        if (!response.ok) {
            // HTTP错误状态
            const errorText = await response.text();
            try {
                const errorJson = JSON.parse(errorText);
                showNotification('保存失败: ' + (errorJson.error || errorJson.message || '未知错误'), 'error');
            } catch (e) {
                showNotification('保存失败: HTTP ' + response.status, 'error');
            }
            return;
        }
        
        const result = await response.json();
        
        if (result.success) {
            showNotification('保存成功', 'success');
        } else {
            showNotification('保存失败: ' + (result.error || result.message || '未知错误'), 'error');
        }
    } catch (error) {
        console.error('保存指标数据失败:', error);
        // 清除"保存中"通知，显示错误通知
        clearNotifications();
        showNotification('保存失败，请检查网络连接', 'error');
    }
}

// 显示指标结果
function displayIndicators(data, analysisTime, fromCache) {
    const resultsContainer = document.getElementById('indicators-results');
    resultsContainer.innerHTML = '';

    // 显示运行时间和缓存提示
    if (analysisTime !== undefined && analysisTime !== null) {
        const timeInfoCol = document.createElement('div');
        timeInfoCol.className = 'col-12';
        const timeInfo = document.createElement('div');
        timeInfo.className = 'alert alert-info';
        timeInfo.style.marginBottom = '15px';
        let timeText = `计算耗时: ${analysisTime} 秒`;
        if (fromCache) {
            timeText += ' (来自缓存)';
        }
        timeInfo.textContent = timeText;
        timeInfoCol.appendChild(timeInfo);
        resultsContainer.appendChild(timeInfoCol);
    }

    // 定义指标卡片顺序
    const indicators = [
        { key: 'indicator_1', icon: '🛍️', color: 'primary' },
        { key: 'indicator_2', icon: '📊', color: 'success' },
        { key: 'indicator_3', icon: '📈', color: 'info' },
        { key: 'indicator_4', icon: '💰', color: 'warning' },
        { key: 'indicator_5', icon: '🔄', color: 'danger' },
        { key: 'indicator_6', icon: '📦', color: 'secondary' },
        { key: 'indicator_7', icon: '📋', color: 'dark' }
    ];

    // 创建指标卡片
    indicators.forEach(indicator => {
        const indicatorData = data[indicator.key];
        if (!indicatorData) return;

        const card = document.createElement('div');
        card.className = 'col-md-6 col-lg-4';

        let valueDisplay = '';
        if (indicator.key === 'indicator_7') {
            // 过程数据展示特殊处理
            const processData = indicatorData.value;
            valueDisplay = `
                <div class="small text-muted">
                    <div>无风险active: ${processData.low_risk_active_count || 0}</div>
                    <div>有风险active: ${processData.high_risk_active_count || 0}</div>
                    <div>限流数据: ${processData.restricted_data_count || 0}</div>
                    <div>未核价数据: ${processData.unpriced_data_count || 0}</div>
                    <div>历史动销被限流: ${processData.restricted_sales_count || 0}</div>
                </div>
            `;
        } else if (indicator.key === 'indicator_4') {
            // 指标4：在售动销品数量 - 显示goods_id列表
            if (indicatorData.goods_ids && Array.isArray(indicatorData.goods_ids) && indicatorData.goods_ids.length > 0) {
                const goodsIds = indicatorData.goods_ids;
                const goodsIdsStr = goodsIds.join(', ');
                const uniqueId = 'goods-ids-4-' + Date.now(); // 使用唯一ID
                valueDisplay = `
                    <div class="h4 mb-0">${indicatorData.value}</div>
                    <div class="mt-2">
                        <button class="btn btn-sm btn-outline-secondary" type="button" data-bs-toggle="collapse" data-bs-target="#${uniqueId}" aria-expanded="false" aria-controls="${uniqueId}">
                            查看goods_id列表 (${goodsIds.length}个)
                        </button>
                        <div class="collapse mt-2" id="${uniqueId}">
                            <div class="card card-body small" style="max-height: 300px; overflow-y: auto; text-align: left; font-family: monospace;">
                                ${goodsIdsStr}
                            </div>
                        </div>
                    </div>
                `;
            } else {
                valueDisplay = `<div class="h4 mb-0">${indicatorData.value}</div>`;
            }
        } else if (indicator.key === 'indicator_5') {
            // 指标5：二次限流动销品占比 - 显示二次限流动销品goods_id列表
            if (indicatorData.goods_ids && Array.isArray(indicatorData.goods_ids) && indicatorData.goods_ids.length > 0) {
                const goodsIds = indicatorData.goods_ids;
                const goodsIdsStr = goodsIds.join(', ');
                const uniqueId = 'goods-ids-5-' + Date.now();
                valueDisplay = `
                    <div class="h4 mb-0">${indicatorData.value}%</div>
                    <div class="mt-2">
                        <button class="btn btn-sm btn-outline-secondary" type="button" data-bs-toggle="collapse" data-bs-target="#${uniqueId}" aria-expanded="false" aria-controls="${uniqueId}">
                            查看二次限流动销品goods_id (${goodsIds.length}个)
                        </button>
                        <div class="collapse mt-2" id="${uniqueId}">
                            <div class="card card-body small" style="max-height: 300px; overflow-y: auto; text-align: left; font-family: monospace;">
                                ${goodsIdsStr}
                            </div>
                        </div>
                    </div>
                `;
            } else {
                valueDisplay = `<div class="h4 mb-0">${indicatorData.value}%</div>`;
            }
        } else {
            valueDisplay = `<div class="h4 mb-0">${indicatorData.value}</div>`;
        }

        card.innerHTML = `
            <div class="card h-100">
                <div class="card-body text-center">
                    <div class="mb-2">
                        <span style="font-size: 2rem;">${indicator.icon}</span>
                    </div>
                    <h6 class="card-title text-${indicator.color}">${indicatorData.name}</h6>
                    ${valueDisplay}
                    <small class="text-muted">${indicatorData.unit}</small>
                </div>
            </div>
        `;

        resultsContainer.appendChild(card);
    });

    // 显示结果区域
    resultsContainer.style.display = 'flex';

    // 处理图表
    const chart30Day = data.indicator_8?.value;
    const chart7Day = data.indicator_9?.value;
    const chartsContainer = document.getElementById('charts-container');

    if (chart30Day) {
        document.getElementById('chart-30day-img').src = `data:image/png;base64,${chart30Day}`;
        document.getElementById('chart-30day-img').style.display = 'block';
        // 移除缓存提示（如果有）
        const cacheHint30 = document.getElementById('chart-30day-cache-hint');
        if (cacheHint30) cacheHint30.remove();
    } else if (fromCache) {
        // 缓存模式下图表为空，显示提示
        document.getElementById('chart-30day-img').style.display = 'none';
        const chart30DayContainer = document.getElementById('chart-30day');
        if (!document.getElementById('chart-30day-cache-hint')) {
            const hint = document.createElement('div');
            hint.id = 'chart-30day-cache-hint';
            hint.className = 'alert alert-warning text-center';
            hint.innerHTML = '<span class="me-2">📊</span>图表未缓存，勾选"非缓存模式"重新计算可获取图表';
            chart30DayContainer.appendChild(hint);
        }
    }

    if (chart7Day) {
        document.getElementById('chart-7day-img').src = `data:image/png;base64,${chart7Day}`;
        document.getElementById('chart-7day-img').style.display = 'block';
        // 移除缓存提示（如果有）
        const cacheHint7 = document.getElementById('chart-7day-cache-hint');
        if (cacheHint7) cacheHint7.remove();
    } else if (fromCache) {
        // 缓存模式下图表为空，显示提示
        document.getElementById('chart-7day-img').style.display = 'none';
        const chart7DayContainer = document.getElementById('chart-7day');
        if (!document.getElementById('chart-7day-cache-hint')) {
            const hint = document.createElement('div');
            hint.id = 'chart-7day-cache-hint';
            hint.className = 'alert alert-warning text-center';
            hint.innerHTML = '<span class="me-2">📊</span>图表未缓存，勾选"非缓存模式"重新计算可获取图表';
            chart7DayContainer.appendChild(hint);
        }
    }

    // 显示图表容器（有图表或缓存模式都显示）
    if (chart30Day || chart7Day || fromCache) {
        chartsContainer.style.display = 'block';
    }
}

// 初始化性能优化
document.addEventListener('DOMContentLoaded', function() {
    // 启用懒加载
    performanceUtils.lazyLoadImages();

    // 优化滚动性能
    const scrollHandler = performanceUtils.throttle(() => {
        // 处理滚动事件
    }, 16); // ~60fps

    // 如果需要滚动优化，可以取消注释
    // window.addEventListener('scroll', scrollHandler, { passive: true });
});


// ===== 功能7：批量国家站点运行 =====

// 显示功能7界面
function showFunction7() {
    // 隐藏其他功能面板
    const function6Content = document.getElementById('function6-content');
    if (function6Content) {
        function6Content.style.display = 'none';
    }
    const function7Content = document.getElementById('function7-content');
    if (function7Content) {
        function7Content.style.display = 'block';
    }
    const functionContent = document.getElementById('function-content');
    if (functionContent) {
        functionContent.style.display = 'none';
    }
    
    // 设置默认日期为昨天
    setBatchDateToYesterday();
    
    // 加载批量国家配置
    loadBatchCountriesConfig();
}

// 设置批量操作日期为昨天
function setBatchDateToYesterday() {
    const yesterday = new Date();
    yesterday.setDate(yesterday.getDate() - 1);
    const dateInput = document.getElementById('batch-date-input');
    if (dateInput) {
        dateInput.value = yesterday.toISOString().split('T')[0];
    }
}

// 加载批量国家配置
async function loadBatchCountriesConfig() {
    try {
        const response = await fetch('/api/function7/config');
        const result = await response.json();
        
        if (result.success) {
            const config = result.data;
            renderBatchTablesList(config.available_tables || [], config.selected_tables || []);
        } else {
            showNotification('加载配置失败: ' + (result.error || '未知错误'), 'error');
        }
    } catch (error) {
        showNotification('加载配置失败: ' + error.message, 'error');
    }
}

// 渲染批量国家表列表
function renderBatchTablesList(availableTables, selectedTables) {
    const listContainer = document.getElementById('batch-tables-list');
    
    if (!availableTables || availableTables.length === 0) {
        listContainer.innerHTML = '<p class="text-muted text-center mb-0" style="grid-column: 1 / -1;">暂无配置的国家表，请先添加</p>';
        return;
    }
    
    let html = '';
    availableTables.forEach(table => {
        const isSelected = selectedTables.includes(table);
        html += `
            <div class="border rounded p-2 d-flex flex-column align-items-center justify-content-center position-relative" 
                 style="min-height: 80px; background-color: ${isSelected ? '#e7f3ff' : '#fff'};">
                <div class="form-check mb-2">
                    <input class="form-check-input batch-table-checkbox" type="checkbox" 
                           value="${table}" id="batch-table-${table}" 
                           ${isSelected ? 'checked' : ''} 
                           onchange="updateBatchSelectedTables()">
                    <label class="form-check-label small" for="batch-table-${table}" style="cursor: pointer;">
                        ${table}
                    </label>
                </div>
                <button class="btn btn-sm btn-outline-danger position-absolute top-0 end-0" 
                        style="padding: 2px 6px; font-size: 10px;"
                        onclick="removeBatchCountryTable('${table}')" 
                        title="删除">
                    <span>🗑️</span>
                </button>
            </div>
        `;
    });
    
    listContainer.innerHTML = html;
}

// 添加国家数据表
async function addBatchCountryTable() {
    const input = document.getElementById('batch-new-table-input');
    const tableName = input.value.trim();
    
    if (!tableName) {
        showNotification('请输入表名', 'warning');
        return;
    }
    
    try {
        const response = await fetch('/api/function7/add_table', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ table_name: tableName })
        });
        
        const result = await response.json();
        
        if (result.success) {
            showNotification(result.message, 'success');
            input.value = '';
            loadBatchCountriesConfig();
        } else {
            showNotification(result.message || result.error, 'error');
        }
    } catch (error) {
        showNotification('添加失败: ' + error.message, 'error');
    }
}

// 移除国家数据表
async function removeBatchCountryTable(tableName) {
    if (!confirm(`确定要移除表 ${tableName} 吗？`)) {
        return;
    }
    
    try {
        const response = await fetch('/api/function7/remove_table', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ table_name: tableName })
        });
        
        const result = await response.json();
        
        if (result.success) {
            showNotification(result.message, 'success');
            loadBatchCountriesConfig();
        } else {
            showNotification(result.message || result.error, 'error');
        }
    } catch (error) {
        showNotification('移除失败: ' + error.message, 'error');
    }
}

// 更新已选中的表
async function updateBatchSelectedTables() {
    const checkboxes = document.querySelectorAll('.batch-table-checkbox:checked');
    const selectedTables = Array.from(checkboxes).map(cb => cb.value);
    
    try {
        const response = await fetch('/api/function7/config', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ selected_tables: selectedTables })
        });
        
        const result = await response.json();
        
        if (!result.success) {
            showNotification('更新选择失败: ' + (result.message || result.error), 'error');
        }
    } catch (error) {
        showNotification('更新选择失败: ' + error.message, 'error');
    }
}

// 全选
function selectAllBatchTables() {
    const checkboxes = document.querySelectorAll('.batch-table-checkbox');
    checkboxes.forEach(cb => cb.checked = true);
    updateBatchSelectedTables();
}

// 取消全选
function deselectAllBatchTables() {
    const checkboxes = document.querySelectorAll('.batch-table-checkbox');
    checkboxes.forEach(cb => cb.checked = false);
    updateBatchSelectedTables();
}

// 验证所有已选中的表
async function validateAllSelectedTables() {
    showNotification('正在验证所选表...', 'info', 0);
    
    try {
        const response = await fetch('/api/function7/validate_all', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        
        const result = await response.json();
        clearNotifications();
        
        if (result.error) {
            showNotification(result.error, 'error');
            return;
        }
        
        // 显示验证结果
        let html = `
            <div class="alert ${result.success ? 'alert-success' : 'alert-warning'}">
                <strong>验证完成：</strong>
                共 ${result.total} 个表，${result.valid} 个有效，${result.invalid} 个无效
            </div>
        `;
        
        if (result.results) {
            html += '<div class="table-responsive"><table class="table table-sm table-bordered">';
            html += '<thead><tr><th>表名</th><th>Traffic</th><th>Sales</th><th>货盘</th><th>商品表</th><th>状态</th></tr></thead>';
            html += '<tbody>';
            
            for (const [tableName, validation] of Object.entries(result.results)) {
                const checks = validation.checks;
                html += `<tr>
                    <td><strong>${tableName}</strong></td>
                    <td>${checks.traffic.exists ? '✅' : '❌'}</td>
                    <td>${checks.sales.exists ? '✅' : '❌'}</td>
                    <td>${checks.pallet.exists ? '✅' : '❌'}</td>
                    <td>${checks.product.exists ? '✅' : '❌'}</td>
                    <td>${validation.success ? '<span class="badge bg-success">通过</span>' : '<span class="badge bg-danger">失败</span>'}</td>
                </tr>`;
                
                if (!validation.success && validation.errors) {
                    html += `<tr><td colspan="6" class="text-danger small">${validation.errors.join('<br>')}</td></tr>`;
                }
            }
            
            html += '</tbody></table></div>';
        }
        
        showBatchOperationResult(html);
        
    } catch (error) {
        clearNotifications();
        showNotification('验证失败: ' + error.message, 'error');
    }
}

// 显示批量操作结果
function showBatchOperationResult(html) {
    const resultDiv = document.getElementById('batch-operation-result');
    const contentDiv = document.getElementById('batch-result-content');
    
    contentDiv.innerHTML = html;
    resultDiv.style.display = 'block';
    
    // 滚动到结果区域
    resultDiv.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

// ----- 功能7：批量进度条与取消 -----
let batchCancelled = false;
let batchProgressModalInstance = null;

function getBatchSelectedTables() {
    const checkboxes = document.querySelectorAll('.batch-table-checkbox:checked');
    return Array.from(checkboxes).map(cb => cb.value);
}

function setBatchCancelled(value) {
    batchCancelled = value;
}

function resetBatchCancelled() {
    batchCancelled = false;
}

function showBatchProgressModal(title) {
    document.getElementById('batchProgressTitle').textContent = title;
    document.getElementById('batchProgressText').textContent = '准备中...';
    document.getElementById('batchProgressPercent').textContent = '0%';
    document.getElementById('batchProgressBar').style.width = '0%';
    document.getElementById('batchProgressBar').textContent = '0%';
    document.getElementById('batchProgressBar').setAttribute('aria-valuenow', 0);
    document.getElementById('batchProgressCurrent').textContent = '—';
    document.getElementById('batchCancelBtn').style.display = 'inline-block';
    document.getElementById('batchProgressCloseBtn').style.display = 'none';
    const el = document.getElementById('batchProgressModal');
    if (!batchProgressModalInstance) {
        batchProgressModalInstance = new bootstrap.Modal(el, { backdrop: 'static', keyboard: false });
    }
    batchProgressModalInstance.show();
}

function updateBatchProgress(current, total, tableName) {
    const pct = total > 0 ? Math.round((current / total) * 100) : 0;
    document.getElementById('batchProgressText').textContent = `已完成 ${current} / ${total}`;
    document.getElementById('batchProgressPercent').textContent = pct + '%';
    const bar = document.getElementById('batchProgressBar');
    bar.style.width = pct + '%';
    bar.textContent = pct + '%';
    bar.setAttribute('aria-valuenow', pct);
    document.getElementById('batchProgressCurrent').textContent = tableName ? '当前: ' + tableName : '—';
}

function hideBatchProgressModal(cancelled) {
    if (batchProgressModalInstance) {
        batchProgressModalInstance.hide();
    }
}

function runBatchWithProgress(options) {
    const { title, tables, apiUrl, getBody, mapResult } = options;
    if (!tables || tables.length === 0) {
        showNotification('没有选中的国家表', 'warning');
        return Promise.resolve(null);
    }
    resetBatchCancelled();
    const abortController = new AbortController();
    showBatchProgressModal(title);
    const cancelBtn = document.getElementById('batchCancelBtn');
    const onceCancel = () => {
        setBatchCancelled(true);
        abortController.abort();
        if (cancelBtn) {
            cancelBtn.onclick = null;
            cancelBtn.disabled = true;
        }
    };
    if (cancelBtn) {
        cancelBtn.disabled = false;
        cancelBtn.onclick = onceCancel;
    }
    const results = {};
    let processed = 0;
    let failed = 0;
    const total = tables.length;
    let promise = Promise.resolve();
    tables.forEach((tableName, index) => {
        promise = promise.then(async () => {
            if (batchCancelled) return;
            updateBatchProgress(index, total, tableName);
            const body = getBody ? getBody(tableName) : { table_name: tableName };
            try {
                const response = await fetch(apiUrl, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(body),
                    signal: abortController.signal
                });
                const data = await response.json();
                const r = mapResult ? mapResult(data) : { success: data.success, message: data.message || data.error };
                results[tableName] = r;
                if (r.success) processed++; else failed++;
            } catch (e) {
                if (e.name === 'AbortError' || batchCancelled) {
                    setBatchCancelled(true);
                    return;
                }
                results[tableName] = { success: false, message: e.message || '请求失败' };
                failed++;
            }
        });
    });
    return promise.then(() => {
        if (cancelBtn) cancelBtn.onclick = null;
        hideBatchProgressModal(batchCancelled);
        return { success: failed === 0 && !batchCancelled, total, processed, failed, results, cancelled: batchCancelled };
    });
}

// 批量刷新Status（串行 + 进度条 + 取消）
async function batchRefreshStatus() {
    if (!confirmBatchOperation('批量刷新')) return;
    clearNotifications();
    const tables = getBatchSelectedTables();
    const result = await runBatchWithProgress({
        title: '批量刷新Status',
        tables,
        apiUrl: '/api/function7/single_refresh',
        getBody: t => ({ table_name: t }),
        mapResult: d => ({ success: d.success, message: d.message || d.error, updated_count: d.updated_count, missing_dates_info: d.missing_dates_info || [] })
    });
    if (result) displayBatchOperationResult('批量刷新Status', result);
    if (batchCancelled) showNotification('已取消批量刷新', 'warning');
}

// 批量快速刷新Status
async function batchQuickRefreshStatus() {
    if (!confirmBatchOperation('批量快速刷新')) return;
    clearNotifications();
    const tables = getBatchSelectedTables();
    const result = await runBatchWithProgress({
        title: '批量快速刷新Status',
        tables,
        apiUrl: '/api/function7/single_quick_refresh',
        getBody: t => ({ table_name: t }),
        mapResult: d => ({ success: d.success, message: d.message || d.error, updated_count: d.updated_count, missing_dates_info: d.missing_dates_info || [] })
    });
    if (result) displayBatchOperationResult('批量快速刷新Status', result);
    if (batchCancelled) showNotification('已取消批量快速刷新', 'warning');
}

// 批量自动更新Reason
async function batchAutoUpdateReason() {
    if (!confirmBatchOperation('批量更新Reason')) return;
    clearNotifications();
    const tables = getBatchSelectedTables();
    const result = await runBatchWithProgress({
        title: '批量更新Reason',
        tables,
        apiUrl: '/api/function7/single_auto_reason',
        getBody: t => ({ table_name: t }),
        mapResult: d => ({ success: d.success, message: d.message || d.error, stats: d.stats, skipped: d.skipped })
    });
    if (result) displayBatchOperationResult('批量自动更新Reason', result);
    if (batchCancelled) showNotification('已取消批量更新Reason', 'warning');
}

// 批量保存指标数据
async function batchSaveIndicatorData() {
    if (!confirmBatchOperation('批量保存指标数据')) return;
    clearNotifications();
    const dateInput = document.getElementById('batch-date-input');
    const targetDate = dateInput ? dateInput.value : null;
    const tables = getBatchSelectedTables();
    const result = await runBatchWithProgress({
        title: '批量保存指标数据',
        tables,
        apiUrl: '/api/function7/single_save_indicator',
        getBody: t => ({ table_name: t, target_date: targetDate }),
        mapResult: d => ({ success: d.success, message: d.message || d.error, calc_time: d.analysis_time })
    });
    if (result) displayBatchOperationResult('批量保存指标数据', result);
    if (batchCancelled) showNotification('已取消批量保存指标', 'warning');
}

// 确认批量操作
function confirmBatchOperation(operationName) {
    const checkboxes = document.querySelectorAll('.batch-table-checkbox:checked');
    if (checkboxes.length === 0) {
        showNotification('请先选择要处理的国家表', 'warning');
        return false;
    }
    
    const selectedTables = Array.from(checkboxes).map(cb => cb.value);
    return confirm(`确定要对以下 ${selectedTables.length} 个国家表执行"${operationName}"操作吗？\n\n${selectedTables.join('\n')}`);
}

// 显示批量操作结果
function displayBatchOperationResult(operationName, result) {
    const cancelled = result.cancelled === true;
    let summary = `共 ${result.total} 个表，成功 ${result.processed} 个，失败 ${result.failed} 个`;
    if (result.skipped !== undefined) summary += `，跳过 ${result.skipped} 个`;
    if (cancelled) summary += '（已取消）';
    let html = `
        <div class="alert ${result.success && !cancelled ? 'alert-success' : 'alert-warning'}">
            <strong>${operationName}${cancelled ? '已取消' : '完成'}：</strong>
            ${summary}
        </div>
    `;
    
    if (result.results) {
        html += '<div class="accordion" id="batchResultAccordion">';
        
        let index = 0;
        for (const [tableName, tableResult] of Object.entries(result.results)) {
            const isSuccess = tableResult.success;
            const isSkipped = tableResult.skipped;
            
            let statusBadge = '';
            if (isSuccess) {
                statusBadge = '<span class="badge bg-success">成功</span>';
            } else if (isSkipped) {
                statusBadge = '<span class="badge bg-warning">跳过</span>';
            } else {
                statusBadge = '<span class="badge bg-danger">失败</span>';
            }
            
            html += `
                <div class="accordion-item">
                    <h2 class="accordion-header" id="heading${index}">
                        <button class="accordion-button ${index > 0 ? 'collapsed' : ''}" type="button" 
                                data-bs-toggle="collapse" data-bs-target="#collapse${index}">
                            <span class="me-2">${tableName}</span>
                            ${statusBadge}
                        </button>
                    </h2>
                    <div id="collapse${index}" class="accordion-collapse collapse ${index === 0 ? 'show' : ''}" 
                         data-bs-parent="#batchResultAccordion">
                        <div class="accordion-body">
                            <p><strong>消息：</strong>${tableResult.message || '无'}</p>
                            ${tableResult.updated_count !== undefined ? `<p><strong>更新数量：</strong>${tableResult.updated_count}</p>` : ''}
                            ${tableResult.stats ? formatBatchStats(tableResult.stats) : ''}
                            ${tableResult.calc_time !== undefined ? `<p><strong>计算耗时：</strong>${tableResult.calc_time}秒</p>` : ''}
                        </div>
                    </div>
                </div>
            `;
            index++;
        }
        
        html += '</div>';
    }
    
    showBatchOperationResult(html);
    
    if (result.success) {
        showNotification(`${operationName}完成！成功处理 ${result.processed} 个表`, 'success');
    } else {
        showNotification(`${operationName}完成，但有 ${result.failed} 个表失败`, 'warning');
    }
}

// 格式化批量操作统计数据
function formatBatchStats(stats) {
    if (!stats) return '';
    
    let html = '<div class="small"><strong>详细统计：</strong><ul class="mb-0">';
    
    for (const [key, value] of Object.entries(stats)) {
        const label = key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
        html += `<li>${label}: ${value}</li>`;
    }
    
    html += '</ul></div>';
    return html;
}