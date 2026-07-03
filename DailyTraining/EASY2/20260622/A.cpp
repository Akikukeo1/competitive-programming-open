#include <iostream>
#include <algorithm>
#include <cctype>
#include <string>

int main() {
    std::string text; std::cin >> text;

    std::transform(text.begin(), text.end(), text.begin(), [](unsigned char c) {return std::toupper(c); });

    std::cout << text << std::endl;

    return 0;
}
