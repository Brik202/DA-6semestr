package main

import (
	"bytes"
	"encoding/csv"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os"
	"strings"
)

type Message struct {
	Role    string `json:"role"`
	Content string `json:"content"`
}

type RequestBody struct {
	Model    string    `json:"model"`
	Messages []Message `json:"messages"`
}

type ResponseBody struct {
	Choices []struct {
		Message Message `json:"message"`
	} `json:"choices"`
}

func loadEnv() {
	data, err := os.ReadFile(".env")
	if err != nil {
		return
	}

	lines := strings.Split(string(data), "\n")

	for _, line := range lines {
		line = strings.TrimSpace(line)

		if line == "" || strings.HasPrefix(line, "#") {
			continue
		}

		parts := strings.SplitN(line, "=", 2)

		if len(parts) != 2 {
			continue
		}

		os.Setenv(
			strings.TrimSpace(parts[0]),
			strings.TrimSpace(parts[1]),
		)
	}
}

func main() {
	loadEnv()

	apiKey := os.Getenv("OPENROUTER_API_KEY")

	if apiKey == "" {
		fmt.Println("Ошибка: OPENROUTER_API_KEY не найден")
		return
	}

	file, err := os.Open("products.csv")
	if err != nil {
		fmt.Println(err)
		return
	}
	defer file.Close()

	reader := csv.NewReader(file)

	rows, err := reader.ReadAll()
	if err != nil {
		fmt.Println(err)
		return
	}

	var descriptions []string

	for i, row := range rows {
		if i == 0 {
			continue
		}

		if len(row) > 1 {
			descriptions = append(descriptions, row[1])
		}
	}

	prompt := `
Извлеки характеристики товаров из описаний.
Верни только JSON-объект без markdown и без пояснений.

Строгий формат ответа:
{
  "items": [
    {
      "id": 1,
      "brand": "Apple",
      "category": "smartphone",
      "price": 799,
      "currency": "USD"
    }
  ]
}

Правила:
- id бери из входных данных;
- brand определи по названию бренда;
- category укажи коротко на английском;
- price должен быть числом;
- currency укажи как в описании товара.

Входные данные:
` + strings.Join(descriptions, "\n")

	requestBody := RequestBody{
		Model: "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free",
		Messages: []Message{
			{
				Role:    "user",
				Content: prompt,
			},
		},
	}

	jsonData, _ := json.Marshal(requestBody)

	req, err := http.NewRequest(
		"POST",
		"https://openrouter.ai/api/v1/chat/completions",
		bytes.NewBuffer(jsonData),
	)
	if err != nil {
		fmt.Println(err)
		return
	}

	req.Header.Set("Authorization", "Bearer "+apiKey)
	req.Header.Set("Content-Type", "application/json")

	client := &http.Client{}

	resp, err := client.Do(req)
	if err != nil {
		fmt.Println(err)
		return
	}
	defer resp.Body.Close()

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		fmt.Println(err)
		return
	}

	if resp.StatusCode != 200 {
		fmt.Println("Ошибка API:")
		fmt.Println("Status:", resp.StatusCode)
		fmt.Println(string(body))
		return
	}

	fmt.Println("Ответ API:")
	fmt.Println(string(body))

	var response ResponseBody

	err = json.Unmarshal(body, &response)
	if err != nil {
		fmt.Println(string(body))
		return
	}

	if len(response.Choices) == 0 {
		fmt.Println("Пустой ответ")
		return
	}

	result := response.Choices[0].Message.Content

	err = os.WriteFile(
		"result.json",
		[]byte(result),
		0644,
	)

	if err != nil {
		fmt.Println(err)
		return
	}

	fmt.Println("Результат сохранён в result.json")
}
