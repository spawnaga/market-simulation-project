using System;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UI;
using System.Linq;
using TMPro;
using UnityEngine.EventSystems;
using UnityEngine.SceneManagement;
using System.Collections;

public class MarketSimulatorReal : MonoBehaviour {
    public int playerPosition = 0; // -1 = short, 0 = flat, 1 = long
    private float entryPrice = 0f;
    private float realizedPnL = 0f;
    public float commissionRate = 0.001f;

    [Range(1, 100)] public int timeSpeed = 1;
    public GPUCandlestickChart chart;
    public float tickInterval = 1.0f, marketSpeed = 1.0f;
    public float timer = 0f;
    public int numTraders;
    public List<TraderReal> traders = new List<TraderReal>();
    public OrderBookReal orderBook = new OrderBookReal();
    public int lastPrice = 3;
    public bool active = false;
    private float positionSize = 0f;
    public int currentCandleIndex = 0;

    [System.Serializable]
    public class CandleArray {
        [SerializeField] public GPUCandlestickChart.Candlestick[] values;
    }

    [SerializeField] public List<CandleArray> futurePaths = new();
    public int saveCandleIndex = -1;

    public LiveCandlestickReal liveCandlestick;
    public BotBatchManager batchManager;

    [Header("UI References (UGUI)")]
    public TextMeshProUGUI positionText;
    public TextMeshProUGUI lastPriceText;
    public TextMeshProUGUI floatingPnLText;
    public TextMeshProUGUI totalPnLText;

    public Button fastForward;
    public Button toggleOrderBarsButton;
    public Button buyButton;
    public Button sellButton;

    private int lastPlayerPosition = 0;
    private int lastLastPrice = -1;
    private float lastFloatingPnL = float.NaN;
    private float lastTotalPnL = float.NaN;
    private int lastTimeSpeed = -1;

    private GPUCandlestickChart.ChartSnapshot chartBackup;
    private GPUCandlestickChart.OrderBookSnapshot orderBackup;
    private bool hasBackup = false;

    void Awake() {
        orderBook.lastTradedPrice = lastPrice;
        active = true;
        InitializeTraders();
        ResetLiveCandlestick();
    }

    void Start() {
        if (fastForward != null)
            AddHoldListener(fastForward.gameObject,
                onDown: () => { active = true; timeSpeed = 100; UpdateUI_Once(); },
                onUp: () => { timeSpeed = 1; UpdateUI_Once(); }
            );

        if (toggleOrderBarsButton != null)
            toggleOrderBarsButton.onClick.AddListener(OnToggleOrderBarsClicked);

        if (buyButton != null)
            buyButton.onClick.AddListener(OnBuyButtonClicked);
        if (sellButton != null)
            sellButton.onClick.AddListener(OnSellButtonClicked);

        UpdateUI_Once();
    }

    private int ticks = 0;
    private bool replaying = false;
    void Update() {
        if (Input.GetKeyDown(KeyCode.Alpha1)) BackupState();
        if (Input.GetKeyDown(KeyCode.Alpha2)) RestoreState();
        if (Input.GetKeyDown(KeyCode.Alpha3)) replaying = !replaying;
        if (replaying) {
            active = true;
            timeSpeed = 250;
            if (chart.candleDataList.Count - (saveCandleIndex + 1 - chart.windowStart) > 40) {
                CaptureFutureRun();
                RestoreState();
            }
        }

        if (Input.GetKeyDown(KeyCode.Space))
            active = !active;
        if (Input.GetKeyDown(KeyCode.Escape)) {
            Application.Quit();
        }
        if (active) {
            timer += (float)timeSpeed / 100f * Time.deltaTime;
            if (timer >= 1f / marketSpeed) {
                timer = 0f;
                ticks++;
                ProcessMarket();
            }

            if (ticks >= 5) {
                ticks = 0;
                FinalizeLiveCandlestick();
                GenerateCandlestick();
                ResetLiveCandlestick();
                chart.UpdateLiveCandle(liveCandlestick.close);

                if (batchManager != null)
                    batchManager.EvaluateBatchStep();
            }
        }

        if (Input.GetKeyDown(KeyCode.B)) {
            Long();
        }

        if (Input.GetKeyDown(KeyCode.S)) {
            Short();
        }

        UpdateUI_Once();
    }

    private void OnToggleOrderBarsClicked() {
        if (chart == null) return;
        chart.drawOrderBars = !chart.drawOrderBars;

        TextMeshProUGUI btnLabel = toggleOrderBarsButton.GetComponentInChildren<TextMeshProUGUI>();
        if (btnLabel != null)
            btnLabel.text = chart.drawOrderBars ? "Hide Order Bars" : "Show Order Bars";
    }

    private void OnBuyButtonClicked() {
        Long();
    }

    private void OnSellButtonClicked() {
        Short();
    }

    private void AddHoldListener(GameObject go, Action onDown, Action onUp) {
        EventTrigger trigger = go.GetComponent<EventTrigger>();
        if (trigger == null) trigger = go.AddComponent<EventTrigger>();
        var entryDown = new EventTrigger.Entry {
            eventID = EventTriggerType.PointerDown
        };
        entryDown.callback.AddListener((data) => { onDown?.Invoke(); });
        trigger.triggers.Add(entryDown);

        var entryUp = new EventTrigger.Entry {
            eventID = EventTriggerType.PointerUp
        };
        entryUp.callback.AddListener((data) => { onUp?.Invoke(); });
        trigger.triggers.Add(entryUp);
    }

    private void UpdateUI_Once() {
        if (playerPosition != lastPlayerPosition) {
            string stateStr = (playerPosition == 1) ? "Long"
                            : (playerPosition == -1) ? "Short"
                            : "Flat";
            if (positionText != null)
                positionText.text = $"Position: {stateStr}";

            lastPlayerPosition = playerPosition;
        }

        int lp = orderBook.lastTradedPrice;
        if (lp != lastLastPrice) {
            if (lastPriceText != null)
                lastPriceText.text = $"Last Price: ${lp / 100f:F2}";
            lastLastPrice = lp;
        }

        float floatingPnL = 0f;
        if (playerPosition == 1) {
            float exitPrice = lp * (1 - commissionRate);
            floatingPnL = (exitPrice - entryPrice) * positionSize;
        } else if (playerPosition == -1) {
            float exitPrice = lp * (1 + commissionRate);
            floatingPnL = (entryPrice - exitPrice) * positionSize;
        }

        if (!Mathf.Approximately(floatingPnL, lastFloatingPnL)) {
            if (floatingPnLText != null) {
                if (Mathf.Approximately(floatingPnL, 0f))
                    floatingPnLText.color = Color.gray;
                else if (floatingPnL > 0f)
                    floatingPnLText.color = new Color(0.3f, 1f, 0.3f);
                else
                    floatingPnLText.color = new Color(1f, 0.4f, 0.4f);

                floatingPnLText.text = $"Floating: {floatingPnL:F2}";
            }

            lastFloatingPnL = floatingPnL;
        }

        float totalPnL = realizedPnL + floatingPnL;
        if (!Mathf.Approximately(totalPnL, lastTotalPnL)) {
            if (totalPnLText != null) {
                if (Mathf.Approximately(totalPnL, 0f))
                    totalPnLText.color = Color.gray;
                else if (totalPnL > 0f)
                    totalPnLText.color = new Color(0.3f, 1f, 0.3f);
                else
                    totalPnLText.color = new Color(1f, 0.4f, 0.4f);

                totalPnLText.text = $"Total PnL: {totalPnL:F2}";
            }

            lastTotalPnL = totalPnL;
        }

        if (timeSpeed != lastTimeSpeed) {
            lastTimeSpeed = timeSpeed;
        }
    }

    void InitializeTraders() {
        traders = new List<TraderReal>();
        System.Random rng = new System.Random();
        AddTraders(numTraders);
    }

    void AddTraders(int count) {
        for (int i = 0; i < count; i++) {
            traders.Add(new TraderReal(orderBook));
        }
    }

    void ProcessMarket() {
        foreach (var trader in traders)
            trader.TryPlaceOrders();

        chart.UpdateLiveCandle(
            liveCandlestick.close,
            liveCandlestick.volume,
            liveCandlestick.high,
            liveCandlestick.low
        );
    }

    void GenerateCandlestick() {
        chart.AddCandlestick(
            liveCandlestick.open,
            liveCandlestick.close,
            liveCandlestick.high,
            liveCandlestick.low,
            liveCandlestick.volume
        );

        orderBook.RecordTrade(liveCandlestick.close);
        currentCandleIndex++;
    }

    void ResetLiveCandlestick() {
        liveCandlestick = new LiveCandlestickReal(lastPrice);
    }

    void FinalizeLiveCandlestick() {
        lastPrice = liveCandlestick.close;
    }

    void BackupState() {
        futurePaths = new();
        chartBackup = chart.GetSnapshot();
        orderBackup = orderBook.GetSnapshot();
        saveCandleIndex = currentCandleIndex;
        hasBackup = true;
        Debug.Log("<color=yellow>[MarketSim]</color> Backup saved.");
    }

    void CaptureFutureRun() {
        var slice = chart.GetCandlesFrom(saveCandleIndex, chart.futureBars);
        if (slice != null)
            futurePaths.Add(new CandleArray { values = slice });
    }

    void RestoreState() {
        if (!hasBackup) return;

        chart.LoadSnapshot(chartBackup);
        orderBook.LoadSnapshot(orderBackup);

        lastPrice = orderBook.lastTradedPrice;
        currentCandleIndex = saveCandleIndex;
        liveCandlestick = new LiveCandlestickReal(lastPrice);
        chart.UpdateLiveCandle(lastPrice);
        timer = 0f;
        ticks = 0;
        realizedPnL = 0f;
        playerPosition = 0;

        UpdateUI_Once();
    }

    private Texture2D MakeTex(int width, int height, Color col) {
        Color[] pix = new Color[width * height];
        for (int i = 0; i < pix.Length; i++) pix[i] = col;

        Texture2D result = new Texture2D(width, height);
        result.SetPixels(pix);
        result.Apply();
        return result;
    }

    public void Long() {
        int lastPrice = orderBook.lastTradedPrice;
        if (playerPosition == 0) {
            entryPrice = lastPrice;
            float totalCost = lastPrice * (1 + commissionRate);
            positionSize = 100f / totalCost;
            playerPosition = 1;
            chart.playerTrades.Add(new GPUCandlestickChart.PlayerTrade(currentCandleIndex, lastPrice, "Buy"));
        } else if (playerPosition == -1) {
            float exitPrice = lastPrice;
            float grossPnL = (entryPrice - exitPrice) * positionSize;
            float commissionCost = (entryPrice + exitPrice) * commissionRate * positionSize;
            realizedPnL += grossPnL - commissionCost;
            playerPosition = 0;
            positionSize = 0f;
            chart.playerTrades.Add(new GPUCandlestickChart.PlayerTrade(currentCandleIndex, lastPrice, "Buy"));
        }
        chart.OnPlayerTradeAdded();
    }

    public void Short() {
        int lastPrice = orderBook.lastTradedPrice;
        if (playerPosition == 0) {
            entryPrice = lastPrice;
            float totalProceeds = lastPrice * (1 - commissionRate);
            positionSize = 100f / totalProceeds;
            playerPosition = -1;
            chart.playerTrades.Add(new GPUCandlestickChart.PlayerTrade(currentCandleIndex, lastPrice, "Sell"));
        } else if (playerPosition == 1) {
            float exitPrice = lastPrice;
            float grossPnL = (exitPrice - entryPrice) * positionSize;
            float commissionCost = (entryPrice + exitPrice) * commissionRate * positionSize;
            realizedPnL += grossPnL - commissionCost;
            playerPosition = 0;
            positionSize = 0f;
            chart.playerTrades.Add(new GPUCandlestickChart.PlayerTrade(currentCandleIndex, lastPrice, "Sell"));
        }
        chart.OnPlayerTradeAdded();
    }
}

[System.Serializable]
public class TraderReal {
    private OrderBookReal orderBook;
    private System.Random rng = new System.Random();

    public TraderReal(OrderBookReal orderBook) {
        this.orderBook = orderBook;
    }

    public void TryPlaceOrders() {
        if (rng.NextDouble() < orderBook.traderActivityRate) PlaceOrders();
    }

    private void PlaceOrders() {
        traderOrder o = DeterminePrice();
        orderBook.PlaceOrder(o.price, o.quantity, o.isBuy);
    }

    public class traderOrder {
        public int price;
        public int quantity;
        public bool isBuy;

        public traderOrder(int p, int q, bool b) {
            price = p;
            quantity = q;
            isBuy = b;
        }
    }

    private traderOrder DeterminePrice() {
        float lastPrice = orderBook.lastTradedPrice;
        int shortMA = orderBook.MA5;
        int longMA = orderBook.MA25;
        float shortTrend = (lastPrice - shortMA) / shortMA;
        float longTrend = (lastPrice - longMA) / longMA;

        bool Maker = rng.NextDouble() < orderBook.proportionMaker;
        float randFactor = 1f + ((float)rng.NextDouble() * 0.02f - 0.01f);
        int randP = Mathf.RoundToInt(lastPrice * randFactor + 0.5f * Mathf.Sign(randFactor - 1f));
        if (Maker) {
            if (randP > lastPrice)
                return new traderOrder(randP, rng.Next(40) + 1, false);
            else
                return new traderOrder(randP, rng.Next(40) + 1, true);
        } else {
            if (randP > lastPrice)
                return new traderOrder(randP, rng.Next(20) + 1, true);
            else
                return new traderOrder(randP, rng.Next(20) + 1, false);
        }
    }
}

[System.Serializable]
public class OrderBookReal {
    public MarketSimulatorReal market;
    public float traderActivityRate = 1f;
    public SortedDictionary<int, int> buyBook = new SortedDictionary<int, int>();
    public SortedDictionary<int, int> sellBook = new SortedDictionary<int, int>();
    public int lastTradedPrice;
    public int BestAsk = int.MaxValue;
    public int BestBid;
    public int[] tradeHistory = new int[100];
    public int tradeIndex = 0, tradeCount = 0;
    public int totalBuyVolume;
    public int totalSellVolume;
    public int MA5 = 3;
    public int MA25 = 3;
    public int MA50 = 3;
    public float imbalance;
    public float proportionMaker;

    public void RecordTrade(int price) {
        tradeHistory[tradeIndex] = price;
        tradeIndex = (tradeIndex + 1) % tradeHistory.Length;
        tradeCount = Math.Min(tradeCount + 1, tradeHistory.Length);

        if (tradeCount >= 5) MA5 = ComputeMovingAverage(5);
        if (tradeCount >= 25) MA25 = ComputeMovingAverage(25);
        if (tradeCount >= 50) MA50 = ComputeMovingAverage(50);
    }

    public int[] GetChronologicalTradeHistory() {
        int[] chronological = new int[tradeHistory.Length];
        int oldestCount = tradeHistory.Length - tradeIndex;
        Array.Copy(tradeHistory, tradeIndex, chronological, 0, oldestCount);
        Array.Copy(tradeHistory, 0, chronological, oldestCount, tradeIndex);
        return chronological;
    }

    public GPUCandlestickChart.OrderBookSnapshot GetSnapshot() {
        return new GPUCandlestickChart.OrderBookSnapshot {
            buyBook = new SortedDictionary<int, int>(buyBook),
            sellBook = new SortedDictionary<int, int>(sellBook),
            lastTradedPrice = lastTradedPrice,
            BestAsk = BestAsk,
            BestBid = BestBid,
            tradeHistory = (int[])tradeHistory.Clone(),
            tradeIndex = tradeIndex,
            tradeCount = tradeCount,
            totalBuyVolume = totalBuyVolume,
            totalSellVolume = totalSellVolume,
            MA5 = MA5,
            MA25 = MA25,
            MA50 = MA50,
            imbalance = imbalance,
            proportionMaker = proportionMaker
        };
    }

    public void LoadSnapshot(GPUCandlestickChart.OrderBookSnapshot s) {
        buyBook = new SortedDictionary<int, int>(s.buyBook);
        sellBook = new SortedDictionary<int, int>(s.sellBook);
        lastTradedPrice = s.lastTradedPrice;
        BestAsk = s.BestAsk;
        BestBid = s.BestBid;

        tradeHistory = (int[])s.tradeHistory.Clone();
        tradeIndex = s.tradeIndex;
        tradeCount = s.tradeCount;

        totalBuyVolume = s.totalBuyVolume;
        totalSellVolume = s.totalSellVolume;

        MA5 = s.MA5; MA25 = s.MA25; MA50 = s.MA50;
        imbalance = s.imbalance;
        proportionMaker = s.proportionMaker;
    }


    private int ComputeMovingAverage(int period) {
        int sum = 0;
        for (int i = 0; i < period; i++) {
            int index = (tradeIndex - 1 - i + tradeHistory.Length) % tradeHistory.Length;
            sum += tradeHistory[index];
        }
        return sum / (int)period;
    }

    public void PlaceOrder(int price, int quantity, bool isBuy) {
        if (price > 0 && quantity > 0) {
            if (isBuy) {//Buy
                if (sellBook.Count > 0 && price > BestAsk)
                    TakeOrder(price, quantity, isBuy);
                else
                    MakeOrder(price, quantity, isBuy);
            } else {//Sell
                if (buyBook.Count > 0 && price < BestBid)
                    TakeOrder(price, quantity, isBuy);
                else
                    MakeOrder(price, quantity, isBuy);
            }
        }
    }

    private void TakeOrder(int p, int q, bool b) {
        int rQ = q;
        lastTradedPrice = market.lastPrice;
        int i = 0;

        while (rQ > 0) {
            i++;
            if (b) {
                if (sellBook.Count == 0) {
                    BestAsk = int.MaxValue;
                    break;
                }
                BestAsk = sellBook.Keys.First();

                if (p < BestAsk)
                    break;
                int aQ = sellBook[BestAsk];
                if (aQ > 0) {
                    int tQ = Mathf.Min(aQ, rQ);
                    sellBook[BestAsk] -= tQ;
                    rQ -= tQ;
                    totalBuyVolume -= tQ;
                    lastTradedPrice = BestAsk;
                    market.liveCandlestick.UpdateWithTrade(BestAsk, tQ);
                    market.chart.UpdateLiveCandle(p, market.liveCandlestick.volume, market.liveCandlestick.high, market.liveCandlestick.low);

                    if (sellBook[BestAsk] <= 0) {
                        sellBook.Remove(BestAsk);
                        BestAsk = sellBook.Count > 0 ? sellBook.Keys.First() : int.MaxValue;
                    }
                }
            } else {
                if (buyBook.Count == 0) {
                    BestBid = 0;
                    break;
                }
                BestBid = buyBook.Keys.Last();

                if (p > BestBid)
                    break;
                int aQ = buyBook[BestBid];
                if (aQ > 0) {
                    int tQ = Mathf.Min(aQ, rQ);
                    buyBook[BestBid] -= tQ;
                    rQ -= tQ;
                    totalSellVolume -= tQ;
                    lastTradedPrice = BestBid;
                    market.liveCandlestick.UpdateWithTrade(BestBid, tQ);
                    market.chart.UpdateLiveCandle(p, market.liveCandlestick.volume, market.liveCandlestick.high, market.liveCandlestick.low);

                    if (buyBook[BestBid] <= 0) {
                        buyBook.Remove(BestBid);
                        BestBid = buyBook.Count > 0 ? buyBook.Keys.Last() : 0;
                    }
                }
            }
        }

        market.lastPrice = lastTradedPrice;
        if (totalBuyVolume + totalSellVolume > 0)
            imbalance = (totalBuyVolume - totalSellVolume) / (totalBuyVolume + totalSellVolume);
        else
            imbalance = 0;

        if (rQ > 0) {
            MakeOrder(p, rQ, b);
        }
    }

    private void MakeOrder(int price, int quantity, bool isBuy) {
        if (isBuy) {
            if (buyBook.ContainsKey(price)) {
                if (buyBook[price] > 0)
                    buyBook[price] += quantity;
                else
                    buyBook[price] = quantity;
            } else
                buyBook[price] = quantity;
            totalBuyVolume += quantity;
            if (price > BestBid)
                BestBid = price;
        } else {
            if (sellBook.ContainsKey(price)) {
                if (sellBook[price] > 0)
                    sellBook[price] += quantity;
                else
                    sellBook[price] = quantity;
            } else
                sellBook[price] = quantity;
            totalSellVolume += quantity;
            if (price < BestAsk)
                BestAsk = price;
        }
    }

    public int GetLastTradedPrice() => lastTradedPrice;
}

public class LiveCandlestickReal {
    public int open, close, high, low, volume;

    public LiveCandlestickReal(int initialPrice) {
        open = close = high = low = initialPrice;
        volume = 0;
    }

    public void UpdateWithTrade(int tradePrice, int volume) {
        close = tradePrice;
        high = Mathf.Max(high, tradePrice);
        low = Mathf.Min(low, tradePrice);
        this.volume += volume;
    }
}
