
var quesno=0;
var score=0;

const questionSet=[
  {
    question:"What is a stock?",
    option1:"A financial instrument that signifies an ownership position in a company.",
    option2:"A fixed regular payment made by a tenant to a landlord.",
    option3:"A bond issued by a government or corporation.",
    option4:"A type of financial asset that can be traded.",
    answer:"option1"
  },
  {
    question:"What does the P/E ratio of a stock signify?",
    option1:"Profit/Earnings of the company",
    option2:"Price to Earnings ratio",
    option3:"Payments to Employees ratio",
    option4:"None of the above",
    answer:"option2"
  },
  {
    question:"A high P/E ratio typically means:",
    option1:"The stock is undervalued",
    option2:"The stock is fairly valued",
    option3:"The stock is overvalued",
    option4:"The stock price is declining",
    answer:"option3"
  },
  {
    question:"What does ROE stand for?",
    option1:"Return Over Exchange",
    option2:"Return On Equity",
    option3:"Ratio Over Earnings",
    option4:"Ratio Of Exchanges",
    answer:"option2"
  },
  {
    question:"Higher ROE indicates:",
    option1:"The company is more efficient in generating profit from shareholders' equity",
    option2:"The company has high debts",
    option3:"The company is not generating enough profit",
    option4:"Both A and B",
    answer:"option1"
  },
  {
    question:"What is a 'bull market'?",
    option1:"A market in which share prices are rising, encouraging buying",
    option2:"A market in which share prices are falling considerably",
    option3:"A market with no significant movement in share prices",
    option4:"None of the above",
    answer:"option1"
  },
  {
    question:"What does the Dividend Yield tell you?",
    option1:"A company's total debt level",
    option2:"How much a company pays out in dividends relative to its share price",
    option3:"Expected volatility of the stock",
    option4:"The company's liquidation value",
    answer:"option2"
  },
  {
    question:"What is 'market capitalization'?",
    option1:"The total value of all commodities in the market",
    option2:"The maximum permissible stock price",
    option3:"The total dollar market value of a company's outstanding shares",
    option4:"The capital required to enter into the market",
    answer:"option3"
  },
  {
    question:"What is Beta in stock market terminology?",
    option1:"The initial stage of a company's development",
    option2:"A measure of a stock's volatility in relation to the overall market",
    option3:"An alpha male investor in finance",
    option4:"The interest rate that banks charge each other",
    answer:"option2"
  },
  {
    question:"What does EPS stand for?",
    option1:"Exponential Profit Surge",
    option2:"Earnings Per Stock",
    option3:"Earnings Per Share",
    option4:"Equal Profit Shares",
    answer:"option3"
  },
  {
    question:"Which statement is true about 'bonds'?",
    option1:"Bonds signify ownership in a company",
    option2:"Bonds are a form of long-term debt",
    option3:"Bonds never pay interest",
    option4:"Bonds are traded exclusively on the stock market",
    answer:"option2"
  },
  {
    question:"Which of these is a fundamental analysis indicator for stocks?",
    option1:"52-week price changes",
    option2:"P/E Ratio",
    option3:"Chart patterns",
    option4:"Price momentum",
    answer:"option2"
  }
  
];

// Initialize the question and options display
function updateQuestionDisplay() {
    document.querySelector("h3").innerHTML = "Q." + (quesno + 1) + " " + questionSet[quesno].question;
    document.querySelector("#option1").innerText = "A. " + questionSet[quesno].option1;
    document.querySelector("#option2").innerHTML = "B. " + questionSet[quesno].option2;
    document.querySelector("#option3").innerHTML = "C. " + questionSet[quesno].option3;
    document.querySelector("#option4").innerHTML = "D. " + questionSet[quesno].option4;
  }
  

  updateQuestionDisplay();
  
  // Adjusted the attemptedQuestion array to have twelve 'false' values for 12 questions
  var attemptedQuestion = new Array(12).fill(false);
  
  
  for (var i = 0; i < 4; i++) {
    document.querySelectorAll(".btn-light")[i].addEventListener("click", function (event) {
      attemptedQuestion[quesno] = true;
  
      var answerFromQuestionSet = questionSet[quesno].answer;
      document.querySelector("#"+answerFromQuestionSet).style.backgroundColor = "#79d70f";
      document.getElementById(questionSet[quesno].answer).disabled = true;
  
      if (event.target.id === questionSet[quesno].answer) {
        score++;
      }
      document.querySelector(".score").innerHTML = score + "/12";
    });
  }
  
  document.querySelector(".next").addEventListener("click", function () {
    // Reset the background color of the previous question's answer
    if (quesno < questionSet.length) {
      document.querySelector("#"+questionSet[quesno].answer).style.backgroundColor = "";
      document.getElementById(questionSet[quesno].answer).disabled = false;
    }
  
    quesno++;
  
    if (quesno < questionSet.length) {
      updateQuestionDisplay();
    } else {
      alert("🎉Congratulations!🎊\nYour Score is " + score + " / 12.");
      window.location.pathname = "/guide";
    }
  
    if (quesno === questionSet.length - 1) {
      document.querySelector(".next").innerHTML = "Finish";
    }
  });
  
  document.querySelector(".prev").addEventListener("click", function () {
    if (quesno > 0) {
      document.querySelector("#"+questionSet[quesno].answer).style.backgroundColor = ""; // Reset background color or leave it empty
      document.getElementById(questionSet[quesno].answer).disabled = false;
  
      quesno--;
  
      updateQuestionDisplay();
    } else {
      alert("You are already on the first question");
    }
  });
  
  updateQuestionDisplay();