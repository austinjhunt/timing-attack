# Code Security Homework Assignment: Timing Attack
In this assignment, you are tasked with thinking like an attacker. To that end, you’ve come to understand there is a web service that is vulnerable to a timing attack. This implementation is particularly obvious and should be relatively easy to break.
Assume that through other means, you have learned three vital pieces of information to assist in gaining access to the system.
1. The alphabet of possible characters is only 0 through 9. Thus a password may be “1234” or “543224” or any other combination of these digits.
2. The entropy of the password is somewhere between 35 and 45 bits. Using what you know about entropy, determining a reasonable range of password lengths is possible.
3. The format of the message is a POST with a “pwd” parameter.
   1. A cURL command to do this would look something like this: `curl -X POST https://qrxjmztf2h.execute-api.us-west-2.amazonaws.com/prod -d '{"pwd":"1111"}' -v`
   2. If the body is in the wrong format we’ll get a 422 returned
   3. If the pwd is wrong, we’ll get a 401
   4. If the pwd is right, we’ll get a 200
4. A test endpoint that behaves exactly the same way as the puzzle can be found at [https://qrxjmztf2h.execute-api.us-west-2.amazonaws.com/prod/example](https://qrxjmztf2h.execute-api.us-west-2.amazonaws.com/prod/example) with a correct password of “42answersall”
   1. Consider using this to test good/bad letters to see the response time
   2. Consider running many tests per letter (in my solution, I used a threadpool to make ~10 requests simultaneously to gather timing information)
   3. Test URL: `curl -X POST https://qrxjmztf2h.execute-api.us-west-2.amazonaws.com/prod/example -d '{"pwd": "42answersall"}' -v`
   
## Recommendations
1. You might sketch out your approach knowing what you do about timing attacks prior to attacking the system.
2. You might consider gathering some metrics about what time differences look like assuming good and bad responses.
3. You might consider trying to determine the key length first.
ASSIGNMENT HOST: https://qrxjmztf2h.execute-api.us-west-2.amazonaws.com/prod
DEMO: https://qrxjmztf2h.execute-api.us-west-2.amazonaws.com/prod/example

## My Approach
At the highest level, here's what we know about how the password is verified on the server: it's checked linearly, character by character. Meaning that the server will take a guessed password `G` as input, and compare it character by character with the real password `R` until it reaches the end of either *or* it reaches a mismatch. Each character comparison takes time, which means a longer response time for one guess G1 than for another guess G2 implies that a longer first substring of G1 is correct than G2. 

As for the password length: the given entropy is $35 \leq (H(X) = \log_2(N)) \leq 45$. Our alphabet length, i.e. our total number of symbols, is 10, so $N = 10^x$ where x gives the bounds for our password length (the number of samples). That is, $35 \leq (H(X) = \log_2(10^x)) \leq 45$. Below is my handwritten solution for finding `x`: 
![finding x by solving the inequality](IMG_5156.jpg)

So, x is either 11, 12, or 13 characters long, which means that in total, we have 
$10^11 + 10^12 + 10^13$ possible passwords.  